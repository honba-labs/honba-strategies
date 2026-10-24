"""Supertrend Strategy - Multi-Timeframe ATR Trailing Stops.

Higher-timeframe (1-hour) trend direction filter combined with
lower-timeframe (5-minute) ATR trailing stops.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Optional

from honba.strategies.base import Strategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class SupertrendConfig(BaseStrategyConfig):
    """Configuration for Supertrend Strategy."""

    # Supertrend parameters
    atr_period: int = 10
    multiplier: Decimal = Decimal("3.0")

    # Multi-timeframe parameters
    trend_timeframe: str = "1h"  # Higher timeframe for trend filter
    entry_timeframe: str = "5m"  # Lower timeframe for entry signals

    # Risk parameters
    risk_per_trade_pct: Decimal = Decimal("0.02")
    max_position_pct: Decimal = Decimal("0.10")
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "supertrend",
        "category": "trend",
        "description": "Multi-timeframe Supertrend with ATR trailing stops and trend filter",
        "tags": ["trend", "supertrend", "atr", "trailing_stop"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.atr_period < 1:
            raise ValueError("atr_period must be >= 1")
        if self.multiplier <= 0:
            raise ValueError("multiplier must be > 0")


@register_strategy("supertrend_follow", "trend", tags=["trend", "supertrend", "atr", "trailing_stop"])
class SupertrendStrategy(Strategy):
    """Multi-timeframe Supertrend Strategy with ATR trailing stops."""

    name = "supertrend_follow"
    Config = SupertrendConfig

    def __init__(self, config: SupertrendConfig) -> None:
        super().__init__(config)
        self.config = config

        self.atr_period = config.atr_period
        self.multiplier = config.multiplier
        self.trend_timeframe = config.trend_timeframe
        self.entry_timeframe = config.entry_timeframe

        # Supertrend state
        self._highs: list[Decimal] = []
        self._lows: list[Decimal] = []
        self._closes: list[Decimal] = []
        self._atr: Optional[Decimal] = None
        self._supertrend: Optional[Decimal] = None
        self._trend: int = 0  # 1 = uptrend, -1 = downtrend

    def on_bar(self, bar) -> None:
        """Process bar and update Supertrend."""
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        self._closes.append(bar.close)

        # Keep history for ATR
        if len(self._closes) > self.atr_period:
            self._highs.pop(0)
            self._lows.pop(0)
            self._closes.pop(0)

        if len(self._closes) < self.atr_period + 1:
            return

        # Calculate ATR
        self._update_atr()
        if self._atr is None:
            return

        # Calculate Supertrend
        self._update_supertrend(bar.close)

        # Check for trend change
        current_pos = self.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")

        # Trend change from down to up - enter long
        if self._trend == 1 and current_pos <= 0:
            self._enter_long(bar.close)
        # Trend change from up to down - enter short
        elif self._trend == -1 and current_pos >= 0:
            self._exit_position(bar.close)

    def _update_atr(self) -> None:
        """Calculate Average True Range."""
        if len(self._closes) < self.atr_period + 1:
            return

        true_ranges = []
        for i in range(-self.atr_period, 0):
            high = self._highs[i]
            low = self._lows[i]
            prev_close = self._closes[i - 1] if i > -self.atr_period else self._closes[0]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        self._atr = sum(true_ranges) / Decimal(str(len(true_ranges)))

    def _update_supertrend(self, close: Decimal) -> None:
        """Update Supertrend value and trend direction."""
        if self._atr is None:
            return

        # Basic upper and lower bands
        basic_upper = (self._highs[-1] + self._lows[-1]) / 2 + self.multiplier * self._atr
        basic_lower = (self._highs[-1] + self._lows[-1]) / 2 - self.multiplier * self._atr

        # Final upper band
        if self._supertrend is None:
            self._supertrend = basic_lower
            self._trend = 1
            return

        # Update trend based on price action
        if close > self._supertrend:
            self._trend = 1
            self._supertrend = max(basic_lower, self._supertrend)
        else:
            self._trend = -1
            self._supertrend = min(basic_upper, self._supertrend)

    def _enter_long(self, price: Decimal) -> None:
        """Enter long position."""
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