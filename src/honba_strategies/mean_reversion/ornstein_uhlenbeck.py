"""Ornstein-Uhlenbeck Mean Reversion Strategy.

Fits continuous-time Ornstein-Uhlenbeck stochastic process:
dX_t = θ(μ - X_t)dt + σdW_t

Computes exact half-life of mean reversion (t_1/2 = ln(2)/θ)
and trades only scrips with half-life < 5 trading days.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import Strategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class OuConfig(BaseStrategyConfig):
    """Configuration for Ornstein-Uhlenbeck Mean Reversion Strategy."""

    # OU process parameters
    lookback_window: int = 60  # Days for parameter estimation

    # Trading thresholds (in standard deviations)
    entry_zscore: Decimal = Decimal("2.0")
    exit_zscore: Decimal = Decimal("0.0")
    stoploss_zscore: Decimal = Decimal("3.0")

    # Half-life constraint
    max_half_life_days: int = 5  # Only trade if half-life < 5 days

    # Risk parameters
    risk_per_trade_pct: Decimal = Decimal("0.02")
    max_position_pct: Decimal = Decimal("0.10")
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "ou_mean_reversion",
        "category": "mean_reversion",
        "description": "Ornstein-Uhlenbeck Mean Reversion - OU process fit with half-life filtering",
        "tags": ["mean_reversion", "ornstein_uhlenbeck", "stochastic", "half_life"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.entry_zscore <= self.exit_zscore:
            raise ValueError("entry_zscore must be > exit_zscore")
        if self.stoploss_zscore <= self.entry_zscore:
            raise ValueError("stoploss_zscore must be > entry_zscore")
        if self.max_half_life_days < 1:
            raise ValueError("max_half_life_days must be >= 1")


@register_strategy("ou_mean_reversion", "mean_reversion", tags=["mean_reversion", "ornstein_uhlenbeck", "stochastic", "half_life"])
class OuMeanReversionStrategy(Strategy):
    """Ornstein-Uhlenbeck Mean Reversion Strategy.

    Fits OU process: dX_t = θ(μ - X_t)dt + σdW_t
    Computes half-life t_1/2 = ln(2)/θ and trades only if t_1/2 < 5 days.
    """

    name = "ou_mean_reversion"
    Config = OuConfig

    def __init__(self, config: OuConfig) -> None:
        super().__init__()
        self.config = config

        self.lookback_window = config.lookback_window
        self.entry_zscore = float(config.entry_zscore)
        self.exit_zscore = float(config.exit_zscore)
        self.stoploss_zscore = float(config.stoploss_zscore)
        self.max_half_life = config.max_half_life_days

        # OU parameters
        self.theta: float | None = None
        self.mu: float | None = None
        self.sigma: float | None = None
        self.half_life: float | None = None

        # Price history
        self._closes: list[Decimal] = []

    def on_bar(self, bar) -> None:
        """Process bar and update OU parameters."""
        self._closes.append(bar.close)

        if len(self._closes) > self.lookback_window:
            self._closes.pop(0)

        # Need enough data for OU estimation
        if len(self._closes) < self.config.lookback_window:
            return

        # Estimate OU parameters
        self._estimate_ou_params()

        if self.theta is None or self.half_life is None:
            return

        # Filter by half-life
        if self.half_life > self.max_half_life:
            return

        # Calculate z-score
        current_price = float(bar.close)
        zscore = self._calculate_zscore(current_price)

        current_pos = self.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")

        # Long entry: zscore <= -entry_zscore (price below mean)
        if self.position(self.instrument_id) <= 0 and zscore <= -self.entry_zscore:
            self._enter_long(bar.close)

        # Short entry: zscore >= entry_zscore (price above mean)
        elif self.position(self.instrument_id) >= 0 and zscore >= self.entry_zscore:
            self._enter_short(bar.close)

        # Exit long
        elif self.position(self.instrument_id) > 0:
            if zscore >= -self.exit_zscore or zscore >= self.stoploss_zscore:
                self._exit_position(bar.close)

        # Exit short
        elif self.position(self.instrument_id) < 0:
            if zscore <= self.exit_zscore or zscore <= -self.stoploss_zscore:
                self._exit_position(bar.close)

    def _estimate_ou_params(self) -> None:
        """Estimate OU parameters using MLE for discrete-time AR(1)."""
        if len(self._closes) < 30:
            return

        prices = [float(p) for p in self._closes[-self.config.lookback_window:]]

        # AR(1): X_t = c + φ * X_{t-1} + ε_t
        # θ = -ln(φ) / dt, μ = c / (1-φ), σ² = var(ε) / (1-φ²) * 2θ
        # For daily data, dt = 1

        n = len(self._closes) - 1
        if n < 10:
            return

        prices = [float(p) for p in self._closes[-self.config.lookback_window:]]
        x = prices[:-1]
        y = prices[1:]

        # OLS estimation
        x_mean = sum(x) / len(x)
        y_mean = sum(y) / len(y)

        num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
        den = sum((x[i] - x_mean) ** 2 for i in range(len(x)))

        if den == 0:
            return

        phi = num / den  # AR(1) coefficient
        c = y_mean - phi * x_mean

        # OU parameters
        # θ = -ln(φ) (for dt=1)
        if phi <= 0 or phi >= 1:
            return

        theta = -math.log(phi)
        mu = c / (1 - phi)

        # Residuals
        residuals = [y[i] - (c + phi * x[i]) for i in range(len(x))]
        sigma_sq = sum(r ** 2 for r in residuals) / len(residuals)
        sigma = math.sqrt(sigma_sq * 2 * theta / (1 - phi ** 2))

        self.theta = theta
        self.mu = mu
        self.sigma = sigma
        self.half_life = math.log(2) / theta if theta > 0 else None

    def _calculate_zscore(self, price: float) -> float:
        """Calculate z-score of current price relative to OU mean."""
        if self.theta is None or self.mu is None or self.sigma is None:
            return 0.0

        # For discrete OU, stationary variance = σ² / (2θ)
        stationary_var = self.sigma ** 2 / (2 * self.theta)
        if stationary_var <= 0:
            return 0.0

        stationary_std = math.sqrt(stationary_var)
        return (price - self.mu) / stationary_std

    def _enter_long(self, price: Decimal) -> None:
        qty = (self.config.capital * self.config.max_position_pct) / price
        if qty > 0:
            self.buy(self.instrument_id, float(qty))

    def _enter_short(self, price: Decimal) -> None:
        qty = (self.config.capital * self.config.max_position_pct) / price
        if qty > 0:
            self.sell(self.instrument_id, float(qty))

    def _exit_position(self, price: Decimal) -> None:
        pos = self.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")
        if pos > 0:
            self.sell(self.instrument_id, float(pos))
        elif pos < 0:
            self.buy(self.instrument_id, abs(float(pos)))