"""Turtle Trading System (Richard Dennis) - System 1 (20-day) and System 2 (55-day).

Classical Donchian breakout channels with volatility-normalized position sizing
based on 20-day ATR (N). Pyramiding logic: add 1 unit every 0.5N profit
up to 4 units; hard stop at 2N from last entry.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import Strategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class TurtleConfig(BaseStrategyConfig):
    """Configuration for Turtle Trading Strategy."""

    # System selection
    system: int = 1  # 1 = 20-day (short), 2 = 55-day (long)

    # Volatility parameters
    atr_period: int = 20
    atr_multiplier: Decimal = Decimal("2.0")  # N = ATR * multiplier
    pyramid_threshold: Decimal = Decimal("0.5")  # Add unit every 0.5N profit
    max_units: int = 4  # Maximum pyramid units

    # Risk parameters
    risk_per_trade_pct: Decimal = Decimal("0.02")  # 2% risk per trade
    max_position_pct: Decimal = Decimal("0.10")
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "turtle_20",
        "category": "trend",
        "description": "Richard Dennis Turtle Trading System - Donchian breakout with ATR position sizing and pyramiding",
        "tags": ["trend", "breakout", "donchian", "turtle"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.system not in (1, 2):
            raise ValueError("system must be 1 (20-day) or 2 (55-day)")
        if self.max_units < 1:
            raise ValueError("max_units must be >= 1")
        if self.risk_per_trade_pct <= 0 or self.risk_per_trade_pct > Decimal("0.1"):
            raise ValueError("risk_per_trade_pct must be in (0, 0.1]")


@register_strategy("turtle_20", "trend", tags=["trend", "breakout", "donchian", "turtle"])
class TurtleStrategy(Strategy):
    """Richard Dennis Turtle Trading System with Donchian breakouts and ATR sizing."""

    name = "turtle_20"
    Config = TurtleConfig

    def __init__(self, config: TurtleConfig) -> None:
        super().__init__()
        self.config = config

        # System parameters
        self.system = config.system
        self.channel_period = 20 if config.system == 1 else 55
        self.exit_period = 10 if config.system == 1 else 20  # System 1: 10-day exit, System 2: 20-day exit

        # ATR parameters
        self.atr_period = config.atr_period
        self.atr_multiplier = config.atr_multiplier
        self.N: Decimal | None = None  # Volatility measure (N = ATR * multiplier)

        # Position management
        self.max_units = config.max_units
        self.pyramid_threshold = config.pyramid_threshold
        self.units_held = 0
        self.entry_price: Decimal | None = None
        self.stop_price: Decimal | None = None

        # Indicators
        self._highs: list[Decimal] = []
        self._lows: list[Decimal] = []
        self._closes: list[Decimal] = []

    def on_bar(self, bar) -> None:
        """Process incoming bar and check for breakout signals."""
        # Store price data for Donchian channel and ATR calculation
        self._highs.append(bar.high)
        self._lows.append(bar.low)
        self._closes.append(bar.close)

        # Keep only required history
        max_period = max(self.channel_period, self.exit_period, self.atr_period)
        if len(self._highs) > max_period:
            self._highs.pop(0)
            self._lows.pop(0)
            self._closes.pop(0)

        # Need enough data for indicators
        if len(self._closes) < self.atr_period:
            return

        # Update ATR (N)
        self._update_atr()

        # Calculate Donchian channels
        upper_channel = max(self._highs[-self.channel_period:])
        lower_channel = min(self._lows[-self.channel_period:])
        exit_upper = max(self._highs[-self.exit_period:])
        exit_lower = min(self._lows[-self.exit_period:])

        current_price = bar.close
        self.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")

        # Check exit conditions first
        if self.units_held > 0:
            self._check_exits(current_price, exit_lower)
        elif self.units_held < 0:
            self._check_exits(current_price, exit_upper)

        # Check entry conditions (only if flat or can pyramid)
        if self.units_held == 0:
            self._check_entry(current_price, upper_channel, lower_channel)
        elif abs(self.units_held) < self.max_units and self.N is not None:
            self._check_pyramid(current_price)

    def _update_atr(self) -> None:
        """Update Average True Range (ATR) for volatility measurement."""
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

        # Simple moving average of true ranges
        self.N = sum(true_ranges) / Decimal(str(len(true_ranges)))

    def _check_entry(self, price: Decimal, upper: Decimal, lower: Decimal) -> None:
        """Check for breakout entry signals."""
        if price >= upper:
            # Long breakout
            self._enter_long(price)
        elif price <= lower:
            # Short breakout
            self._enter_short(price)

    def _enter_long(self, price: Decimal) -> None:
        """Enter long position with initial unit."""
        if self.N is None:
            return

        # Calculate position size: risk_per_trade / N
        risk_amount = self.config.capital * self.config.risk_per_trade_pct
        unit_size = risk_amount / (self.N * self.atr_multiplier)

        # Cap at max position
        max_qty = (self.config.capital * self.config.max_position_pct) / price
        unit_size = min(unit_size, max_qty)

        if unit_size <= 0:
            return

        self.buy(self.instrument_id, float(unit_size))
        self.units_held = 1
        self.entry_price = price
        self.stop_price = price - (self.N * self.atr_multiplier * Decimal("2"))

    def _enter_short(self, price: Decimal) -> None:
        """Enter short position with initial unit."""
        if self.N is None:
            return

        risk_amount = self.config.capital * self.config.risk_per_trade_pct
        unit_size = risk_amount / (self.N * self.atr_multiplier)

        max_qty = (self.config.capital * self.config.max_position_pct) / price
        unit_size = min(unit_size, max_qty)

        if unit_size <= 0:
            return

        self.sell(self.instrument_id, float(unit_size))
        self.units_held = -1
        self.entry_price = price
        self.stop_price = price + (self.N * self.atr_multiplier * Decimal("2"))

    def _check_pyramid(self, price: Decimal) -> None:
        """Check if we should add to position (pyramiding)."""
        if self.N is None or self.entry_price is None:
            return

        # For long positions
        if self.units_held > 0:
            profit = price - self.entry_price
            if profit >= self.N * self.atr_multiplier * self.pyramid_threshold:
                self._add_unit(price, "long")

        # For short positions
        elif self.units_held < 0:
            profit = self.entry_price - price
            if profit >= self.N * self.atr_multiplier * self.pyramid_threshold:
                self._add_unit(price, "short")

    def _add_unit(self, price: Decimal, direction: str) -> None:
        """Add a pyramid unit."""
        if abs(self.units_held) >= self.max_units:
            return

        if self.N is None:
            return

        risk_amount = self.config.capital * self.config.risk_per_trade_pct
        unit_size = risk_amount / (self.N * self.atr_multiplier)

        current_price = price
        max_qty = (self.config.capital * self.config.max_position_pct) / current_price
        unit_size = min(unit_size, max_qty)

        if unit_size <= 0:
            return

        if direction == "long":
            self.buy(self.instrument_id, float(unit_size))
            self.units_held += 1
            self.entry_price = price  # Update average entry price
            self.stop_price = price - (self.N * self.atr_multiplier * Decimal("2"))
        else:
            self.sell(self.instrument_id, float(unit_size))
            self.units_held -= 1
            self.entry_price = price
            self.stop_price = price + (self.N * self.atr_multiplier * Decimal("2"))

    def _check_exits(self, price: Decimal, exit_channel: Decimal) -> None:
        """Check for exit signals."""
        # Hard stop
        if self.stop_price is not None:
            if (self.units_held > 0 and price <= self.stop_price) or (self.units_held < 0 and price >= self.stop_price):
                self._exit_all(price, "STOP")
                return

        # Channel exit
        if (self.units_held > 0 and price <= exit_channel) or (self.units_held < 0 and price >= exit_channel):
            self._exit_all(price, "CHANNEL_EXIT")

    def _exit_all(self, price: Decimal, reason: str) -> None:
        """Exit all units."""
        if self.units_held > 0:
            self.sell(self.instrument_id, abs(float(self.position(self.instrument_id))))
        elif self.units_held < 0:
            self.buy(self.instrument_id, abs(float(self.position(self.instrument_id))))

        self.units_held = 0
        self.entry_price = None
        self.stop_price = None
        self.log_event(f"TURTLE_EXIT_{reason}", price=price)