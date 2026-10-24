"""KAMA (Kaufman Adaptive Moving Average) Crossover Strategy.

Dual KAMA strategy adapting to market Efficiency Ratio (ER).
Suppresses whipsaw signals during sideways consolidation; reacts sharply during fast regime shifts.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Optional

from honba.strategies.base import Strategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class KamaConfig(BaseStrategyConfig):
    """Configuration for KAMA Crossover Strategy."""

    # KAMA parameters
    fast_period: int = 10  # Fast KAMA period
    slow_period: int = 30  # Slow KAMA period
    er_period: int = 10  # Efficiency Ratio period

    # Risk parameters
    risk_per_trade_pct: Decimal = Decimal("0.02")
    max_position_pct: Decimal = Decimal("0.10")
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "kama_crossover",
        "category": "trend",
        "description": "KAMA Crossover - Dual Kaufman Adaptive Moving Average adapting to market Efficiency Ratio",
        "tags": ["trend", "kama", "adaptive", "crossover"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.fast_period >= self.slow_period:
            raise ValueError("fast_period must be less than slow_period")
        if self.er_period < 2:
            raise ValueError("er_period must be >= 2")


@register_strategy("kama_crossover", "trend", tags=["trend", "kama", "adaptive", "crossover"])
class KamaCrossoverStrategy(Strategy):
    """KAMA (Kaufman Adaptive Moving Average) Crossover Strategy.

    Uses dual KAMA with different speeds. KAMA adapts to market noise
    via Efficiency Ratio (ER), suppressing whipsaws in sideways markets.
    """

    name = "kama_crossover"
    Config = KamaConfig

    def __init__(self, config: KamaConfig) -> None:
        super().__init__(config)
        self.config = config

        self.fast_period = config.fast_period
        self.slow_period = config.slow_period
        self.er_period = config.er_period

        # KAMA state
        self.fast_kama: Optional[Decimal] = None
        self.slow_kama: Optional[Decimal] = None
        self.fast_sc: Optional[Decimal] = None
        self.slow_sc: Optional[Decimal] = None

        # Price history for ER calculation
        self._closes: list[Decimal] = []

    def on_bar(self, bar) -> None:
        """Process bar and update KAMA values."""
        self._closes.append(bar.close)

        # Need enough data for slow KAMA
        if len(self._closes) < self.slow_period + self.er_period:
            return

        # Calculate Efficiency Ratio
        er = self._calculate_er()
        if er is None:
            return

        # Calculate Smoothing Constants
        fast_sc = self._calculate_sc(er, self.fast_period)
        slow_sc = self._calculate_sc(er, self.slow_period)

        # Update KAMA values
        if self.fast_kama is None:
            self.fast_kama = self._closes[-1]
            self.slow_kama = self._closes[-1]
            self.fast_sc = fast_sc
            self.slow_sc = slow_sc
            return

        self.fast_kama = self.fast_kama + fast_sc * (bar.close - self.fast_kama)
        self.slow_kama = self.slow_kama + slow_sc * (bar.close - self.slow_kama)

        # Check for crossover
        prev_fast = self.fast_kama - fast_sc * (bar.close - self.fast_kama)
        prev_slow = self.slow_kama - slow_sc * (bar.close - self.slow_kama)

        current_pos = self.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")

        # Golden cross: fast crosses above slow
        if prev_fast <= prev_slow and self.fast_kama > self.slow_kama:
            if current_pos <= 0:
                self._enter_long(bar.close)

        # Death cross: fast crosses below slow
        elif prev_fast >= prev_slow and self.fast_kama < self.slow_kama:
            if current_pos >= 0:
                self._exit_position(bar.close)

    def _calculate_er(self) -> Optional[Decimal]:
        """Calculate Efficiency Ratio (ER) over er_period."""
        if len(self._closes) < self.er_period + 1:
            return None

        # Direction = |close - close[er_period]|
        direction = abs(self._closes[-1] - self._closes[-self.er_period - 1])

        # Volatility = sum(|close[i] - close[i-1]|) over er_period
        volatility = sum(
            abs(self._closes[-i] - self._closes[-i - 1])
            for i in range(1, self.er_period + 1)
        )

        if volatility == 0:
            return Decimal("0")

        return direction / volatility

    def _calculate_sc(self, er: Decimal, period: int) -> Decimal:
        """Calculate Smoothing Constant (SC) for given ER and period."""
        # Fast SC: 2/(period+1), Slow SC: 2/(period+1)
        # SC = [ER * (fast_sc - slow_sc) + slow_sc]^2
        fast_alpha = Decimal("2") / Decimal(str(period + 1))
        slow_alpha = Decimal("2") / Decimal(str(period + 1))

        # KAMA uses variable SC based on ER
        # SC = [ER * (fast_alpha - slow_alpha) + slow_alpha]^2
        sc = (er * (fast_alpha - slow_alpha) + slow_alpha) ** 2
        return sc

    def _enter_long(self, price: Decimal) -> None:
        """Enter long position."""
        risk_amount = self.config.capital * self.config.risk_per_trade_pct
        # Simple position sizing - can be enhanced
        qty = (self.config.capital * self.config.max_position_pct) / price

        if qty > 0:
            self.buy(self.instrument_id, float(qty))

    def _exit_position(self, price: Decimal) -> None:
        """Exit position."""
        pos = self.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")
        if pos > 0:
            self.sell(self.instrument_id, float(pos))
        elif pos < 0:
            self.buy(self.instrument_id, abs(float(pos)))