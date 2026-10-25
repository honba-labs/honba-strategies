"""VWAP Band Reversion Mean Reversion Strategy.

Intraday mean reversion when price deviates >= 2.5σ from session VWAP.
Strict 15:20 IST auto-square-off enforcement for MIS equity.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import Strategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class VwapBandConfig(BaseStrategyConfig):
    """Configuration for VWAP Band Reversion Strategy."""

    # VWAP parameters
    vwap_period: int = 1  # Session VWAP (1 day)
    std_dev_mult: Decimal = Decimal("2.5")

    # Session parameters
    entry_cutoff: str = "15:00"  # IST entry cutoff
    square_off: str = "15:20"  # IST auto square-off

    # Risk parameters
    risk_per_trade_pct: Decimal = Decimal("0.02")
    max_position_pct: Decimal = Decimal("0.10")
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "vwap_bands",
        "category": "mean_reversion",
        "description": "Intraday mean reversion to session VWAP with entry cutoff and 15:20 square-off",
        "tags": ["mean_reversion", "vwap", "bands", "intraday"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.std_dev_mult <= 0:
            raise ValueError("std_dev_mult must be > 0")


@register_strategy("vwap_bands", "mean_reversion", tags=["mean_reversion", "vwap", "bands", "intraday"])
class VwapBandReversionStrategy(Strategy):
    """VWAP Band Reversion Strategy.

    Trades intraday mean reversion when price deviates >= 2.5σ from session VWAP.
    Strict 15:20 IST intraday square-off enforcement.
    """

    name = "vwap_bands"
    Config = VwapBandConfig

    def __init__(self, config: VwapBandConfig) -> None:
        super().__init__()
        self.config = config

        self.std_dev_mult = config.std_dev_mult
        self.entry_cutoff = config.entry_cutoff
        self.square_off = config.square_off

        # VWAP state
        self._typical_prices: list[Decimal] = []
        self._volumes: list[Decimal] = []
        self._vwap: Decimal | None = None
        self._std_dev: Decimal | None = None
        self._upper_band: Decimal | None = None
        self._lower_band: Decimal | None = None
        self._vwap_value: Decimal | None = None

    def on_bar(self, bar) -> None:
        """Process bar and update VWAP bands."""
        # For intraday, we use typical price = (H+L+C)/3
        typical_price = (bar.high + bar.low + bar.close) / Decimal("3")
        volume = bar.volume

        self._typical_prices.append(typical_price)
        self._volumes.append(volume)

        # Calculate session VWAP
        self._update_vwap()

        if self._vwap_value is None or self._std_dev is None:
            return

        current_pos = self.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")
        price = bar.close

        # Check for square-off time
        if self._is_square_off_time(bar):
            if self.position(self.instrument_id) != 0:
                self._exit_all(bar.close)
            return

        # Check entry cutoff
        if self._is_after_entry_cutoff(bar):
            return

        # Long entry: price below lower band
        if self._lower_band is not None and bar.close <= self._lower_band:
            if self.position(self.instrument_id) <= 0:
                self._enter_long(bar.close)

        # Short entry: price above upper band
        elif self._upper_band is not None and bar.close >= self._upper_band:
            if self.position(self.instrument_id) >= 0:
                self._enter_short(bar.close)

        # Exit conditions
        elif self.position(self.instrument_id) > 0:
            if bar.close >= self._vwap_value:
                self._exit_position(bar.close)
        elif self.position(self.instrument_id) < 0:
            if bar.close <= self._vwap_value:
                self._exit_position(bar.close)

    def _update_vwap(self) -> None:
        """Calculate session VWAP and standard deviation bands."""
        if not self._typical_prices:
            return

        # VWAP = sum(price * volume) / sum(volume)
        total_pv = sum(p * v for p, v in zip(self._typical_prices, self._volumes))
        total_v = sum(self._volumes)

        if total_v == 0:
            return

        self._vwap_value = total_pv / total_v

        # Standard deviation of typical prices
        if len(self._typical_prices) < 2:
            return

        mean = sum(self._typical_prices) / Decimal(str(len(self._typical_prices)))
        variance = sum((x - self._vwap_value) ** 2 for x in self._typical_prices) / Decimal(str(len(self._typical_prices)))
        self._std_dev = variance.sqrt()

        # Bands
        self._upper_band = self._vwap_value + (self.config.std_dev_mult * self._std_dev)
        self._lower_band = self._vwap_value - (self.config.std_dev_mult * self._std_dev)

    def _is_square_off_time(self, bar) -> bool:
        """Check if it's square-off time (15:20 IST)."""
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour >= 15 and bar.ts.minute >= 20
        return False

    def _is_after_entry_cutoff(self, bar) -> bool:
        """Check if past entry cutoff time (15:00 IST)."""
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour >= 15 and bar.ts.minute >= 0
        return False

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

    def _exit_all(self, price: Decimal) -> None:
        pos = self.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")
        if pos > 0:
            self.sell(self.instrument_id, float(pos))
        elif pos < 0:
            self.buy(self.instrument_id, abs(float(pos)))