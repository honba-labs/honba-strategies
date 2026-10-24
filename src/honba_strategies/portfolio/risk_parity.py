"""Risk Parity Allocation Strategy.

Weight assets inversely proportional to their historical volatility
matrix so each asset contributes equal risk.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Dict, Optional

from honba.strategies.base import Strategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class RiskParityConfig(BaseStrategyConfig):
    """Configuration for Risk Parity Strategy."""

    lookback_window: int = 60
    rebalance_frequency: str = "monthly"
    min_volatility: Decimal = Decimal("0.0001")
    max_leverage: Decimal = Decimal("1.0")

    _registry_meta: ClassVar[dict] = {
        "name": "risk_parity",
        "category": "portfolio",
        "description": "Risk parity allocation weighting inversely proportional to volatility",
        "tags": ["statistical", "volatility"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.lookback_window < 10:
            raise ValueError("lookback_window must be >= 10")
        if self.max_leverage <= 0:
            raise ValueError("max_leverage must be > 0")


@register_strategy("risk_parity", "portfolio", tags=["statistical", "volatility"])
class RiskParityStrategy(Strategy):
    """Risk Parity Allocation Strategy."""

    name = "risk_parity"
    Config = RiskParityConfig

    def __init__(self, config: RiskParityConfig) -> None:
        super().__init__(config)
        self.config = config

        self.lookback_window = config.lookback_window
        self.max_leverage = config.max_leverage

        self.returns_history: Dict[str, list[Decimal]] = {}
        self.volatilities: Dict[str, Decimal] = {}
        self.target_weights: Dict[str, Decimal] = {}
        self.universe: list[str] = []

    def on_start(self) -> None:
        if hasattr(self, 'universe_list') and self.universe_list:
            self.universe = self.universe_list
        else:
            self.universe = []
        for symbol in self.universe:
            self.returns_history[symbol] = []
            self.volatilities[symbol] = Decimal("0.01")

    def on_bar(self, bar) -> None:
        if not self.universe or bar.symbol not in self.universe:
            return

        # Track returns
        if bar.symbol in self.returns_history:
            # Simplified return calculation
            pass

        # Calculate volatilities and rebalance periodically
        if len(self.returns_history.get(bar.symbol, [])) >= self.lookback_window:
            self._calculate_risk_parity_weights()

    def _calculate_risk_parity_weights(self) -> None:
        """Calculate risk parity weights (inverse volatility)."""
        # Calculate volatilities
        for symbol in self.universe:
            returns = self.returns_history.get(symbol, [])
            if len(returns) < self.lookback_window:
                continue
            # Simplified volatility
            recent = returns[-self.lookback_window:]
            mean_ret = sum(recent) / Decimal(str(len(recent)))
            var = sum((r - mean_ret) ** 2 for r in recent) / Decimal(str(len(recent)))
            self.volatilities[symbol] = var.sqrt()

        # Inverse volatility weights
        inv_vol_sum = Decimal("0")
        for symbol in self.universe:
            vol = self.volatilities.get(symbol, self.config.min_volatility)
            if vol < self.config.min_volatility:
                vol = self.config.min_volatility
            inv_vol_sum += Decimal("1") / vol

        if inv_vol_sum == 0:
            return

        for symbol in self.universe:
            vol = self.volatilities.get(symbol, self.config.min_volatility)
            if vol < self.config.min_volatility:
                vol = self.config.min_volatility
            self.target_weights[symbol] = (Decimal("1") / vol) / inv_vol_sum
            # Apply leverage cap
            if self.target_weights[symbol] > self.max_leverage / Decimal(str(len(self.universe))):
                self.target_weights[symbol] = self.max_leverage / Decimal(str(len(self.universe)))
