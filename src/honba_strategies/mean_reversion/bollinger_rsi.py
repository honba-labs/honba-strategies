"""Bollinger Band + RSI Exhaustion Mean Reversion Strategy.

Long entry when price closes below Lower Bollinger Band (2σ) and RSI < 25.
Exit on reversion to Middle Band (20 SMA) or opposite band touch.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import Strategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class BollingerRsiConfig(BaseStrategyConfig):
    """Configuration for Bollinger Band + RSI Mean Reversion Strategy."""

    # Bollinger Band parameters
    bb_period: int = 20
    bb_std_dev: Decimal = Decimal("2.0")

    # RSI parameters
    rsi_period: int = 14
    rsi_oversold: Decimal = Decimal("25")
    rsi_overbought: Decimal = Decimal("75")

    # Risk parameters
    risk_per_trade_pct: Decimal = Decimal("0.02")
    max_position_pct: Decimal = Decimal("0.10")
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "bollinger_rsi",
        "category": "mean_reversion",
        "description": "Bollinger Band + RSI Exhaustion - Long when price < Lower Band and RSI < 25",
        "tags": ["mean_reversion", "bollinger", "rsi", "exhaustion"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.bb_period < 2:
            raise ValueError("bb_period must be >= 2")
        if self.bb_std_dev <= 0:
            raise ValueError("bb_std_dev must be > 0")
        if not (0 < self.rsi_oversold < self.rsi_overbought < 100):
            raise ValueError("rsi_oversold must be < rsi_overbought and both in (0, 100)")


@register_strategy("bollinger_rsi", "mean_reversion", tags=["mean_reversion", "bollinger", "rsi", "exhaustion"])
class BollingerRsiStrategy(Strategy):
    """Bollinger Band + RSI Exhaustion Mean Reversion Strategy.

    Long entry when price closes below Lower Bollinger Band (2σ) and RSI < 25.
    Exit on reversion to Middle Band (20 SMA) or opposite band touch.
    """

    name = "bollinger_rsi"
    Config = BollingerRsiConfig

    def __init__(self, config: BollingerRsiConfig) -> None:
        super().__init__()
        self.config = config
        self.instrument_id = config.instrument_id

        self.bb_period = config.bb_period
        self.bb_std_dev = config.bb_std_dev
        self.rsi_period = config.rsi_period
        self.rsi_oversold = config.rsi_oversold
        self.rsi_overbought = config.rsi_overbought

        # State for indicators
        self._closes: list[Decimal] = []
        self._bb_upper: Decimal | None = None
        self._bb_middle: Decimal | None = None
        self._bb_lower: Decimal | None = None
        self._rsi: Decimal | None = None

    def on_bar(self, bar) -> None:
        """Process incoming bar and update indicators."""
        self._closes.append(Decimal(str(bar.close)))

        # Keep sufficient history
        max_period = max(self.bb_period, self.rsi_period)
        if len(self._closes) > max_period + 5:
            self._closes.pop(0)

        # Need enough data for indicators
        if len(self._closes) < max(self.bb_period, self.rsi_period):
            return

        # Update Bollinger Bands
        self._update_bollinger()

        # Update RSI
        self._update_rsi()

        if self._bb_upper is None or self._bb_middle is None or self._bb_lower is None or self._rsi is None:
            return

        current_pos = self.position(self.instrument_id)
        price = Decimal(str(bar.close))

        # Long entry: price below lower band AND RSI oversold
        if current_pos <= 0 and price <= self._bb_lower and self._rsi <= self.rsi_oversold:
            self._enter_long(price)

        # Exit long: price returns to middle band or touches upper band
        elif current_pos > 0 and (price >= self._bb_middle or price >= self._bb_upper):
            self._exit_position(price)

    def _update_bollinger(self) -> None:
        """Calculate Bollinger Bands."""
        if len(self._closes) < self.bb_period:
            return

        recent = self._closes[-self.bb_period:]
        sma = sum(recent) / Decimal(str(len(recent)))

        # Standard deviation
        variance = sum((x - sma) ** 2 for x in recent) / Decimal(str(len(recent)))
        std_dev = variance.sqrt()

        self._bb_middle = sma
        self._bb_upper = sma + (self.bb_std_dev * std_dev)
        self._bb_lower = sma - (self.bb_std_dev * std_dev)

    def _update_rsi(self) -> None:
        """Calculate RSI using Wilder's smoothing."""
        if len(self._closes) < self.rsi_period + 1:
            return

        gains = []
        losses = []
        for i in range(-self.rsi_period, 0):
            change = self._closes[i] - self._closes[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(Decimal("0"))
            else:
                gains.append(Decimal("0"))
                losses.append(abs(change))

        avg_gain = sum(gains) / Decimal(str(len(gains)))
        avg_loss = sum(losses) / Decimal(str(len(losses)))

        if avg_loss == 0:
            self._rsi = Decimal("100")
        else:
            rs = avg_gain / avg_loss
            self._rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))

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