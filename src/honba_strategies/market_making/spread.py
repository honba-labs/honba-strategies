"""Passive Spread Quoting Strategy.

Places continuous bid at Best Bid and ask at Best Ask; automatically
cancel-replace on market depth shifts. Guards against adverse selection
using Order Book Imbalance (OBI) indicator from honba-me.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import QuotingStrategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class SpreadQuotingConfig(BaseStrategyConfig):
    """Configuration for Passive Spread Quoting Strategy."""

    # Quoting parameters
    spread_bps: Decimal = Decimal("10")  # Target spread in basis points
    quote_quantity: Decimal = Decimal("100")  # Quantity per quote
    max_inventory: Decimal = Decimal("1000")  # Max net position

    # Risk parameters
    obi_threshold: Decimal = Decimal("0.3")  # OBI threshold for adverse selection guard
    max_position_pct: Decimal = Decimal("0.05")
    freeze_limit: int = 1800

    # Order management
    price_tolerance: Decimal = Decimal("0.5")  # Max price drift before requote
    requote_interval_sec: int = 1  # Minimum seconds between requotes

    _registry_meta: ClassVar[dict] = {
        "name": "spread_quoting",
        "category": "market_making",
        "description": "Passive spread quoting with OBI adverse selection guard",
        "tags": ["market_making", "quoting", "spread"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.spread_bps <= 0:
            raise ValueError("spread_bps must be positive")
        if self.quote_quantity <= 0:
            raise ValueError("quote_quantity must be positive")
        if not (Decimal("0") < self.obi_threshold < Decimal("1")):
            raise ValueError("obi_threshold must be in (0, 1)")


@register_strategy("spread_quoting", "market_making", tags=["market_making", "quoting", "spread"])
class SpreadQuotingStrategy(QuotingStrategy):
    """Passive spread quoting with OBI adverse selection guard."""

    name = "spread_quoting"
    Config = SpreadQuotingConfig

    def __init__(self, config: SpreadQuotingConfig) -> None:
        super().__init__(
            quoting_side="BOTH",
            quoting_quantity=config.quote_quantity,
            price_tolerance=config.price_tolerance,
        )
        self.config = config
        self.spread_bps = config.spread_bps
        self.max_inventory = config.max_inventory
        self.obi_threshold = config.obi_threshold
        self.requote_interval_sec = config.requote_interval_sec
        self._last_requote_ts: int | None = None

    def on_quote(self, quote) -> None:
        """Process quote updates and manage quotes."""
        # Check OBI for adverse selection
        obi = self._calculate_obi(quote)
        if abs(obi) > self.obi_threshold:
            self._pull_quotes()
            return

        # Calculate target prices
        mid = (quote.bid_price + quote.ask_price) / 2
        half_spread = mid * (self.spread_bps / Decimal("10000")) / 2
        bid_price = mid - half_spread
        ask_price = mid + half_spread

        # Check inventory limits
        current_pos = self.ctx.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")
        
        if current_pos >= self.max_inventory:
            # Reduce ask size or pull ask
            ask_price = None
        elif current_pos <= -self.max_inventory:
            # Reduce bid size or pull bid
            bid_price = None

        # Update quotes
        if bid_price is not None:
            self.update_quote(
                instrument_id=self.instrument_id,
                target_price=bid_price,
                target_qty=self.config.quote_quantity,
            )
        if ask_price is not None:
            self.update_quote(
                instrument_id=self.instrument_id,
                target_price=ask_price,
                target_qty=self.config.quote_quantity,
            )

    def _calculate_obi(self, quote) -> Decimal:
        """Calculate Order Book Imbalance from quote."""
        if quote.bid_qty + quote.ask_qty == 0:
            return Decimal("0")
        return (quote.bid_qty - quote.ask_qty) / (quote.bid_qty + quote.ask_qty)

    def _pull_quotes(self) -> None:
        """Pull all active quotes."""
        if self._active_intent is not None:
            self.cancel(self._active_intent)
            self._active_intent = None
            self._quoted_price = None
            self._quoted_qty = None

    def on_fill(self, fill) -> None:
        """Update inventory tracking on fill."""
        super().on_fill(fill)