"""Ladder Quoting Strategy.

Multi-level grid quoting across L depth levels with position size decay.
Inventory-aware queue position tracking and layer rebalancing.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import QuotingStrategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class LadderQuotingConfig(BaseStrategyConfig):
    """Configuration for Ladder Quoting Strategy."""

    # Ladder parameters
    num_levels: int = 5  # Number of price levels on each side
    level_spread_bps: Decimal = Decimal("5")  # Spread between levels (bps)
    base_quantity: Decimal = Decimal("100")  # Quantity at level 0
    quantity_decay: Decimal = Decimal("0.5")  # Geometric decay factor per level

    # Risk parameters
    max_total_inventory: Decimal = Decimal("5000")
    max_position_pct: Decimal = Decimal("0.05")
    freeze_limit: int = 1800

    # Rebalancing
    rebalance_threshold_bps: Decimal = Decimal("10")  # Rebalance when price moves this much
    max_levels_active: int = 3  # Max active levels per side

    _registry_meta: ClassVar[dict] = {
        "name": "ladder_quoting",
        "category": "market_making",
        "description": "Multi-level ladder quoting with geometric size decay and inventory awareness",
        "tags": ["market_making", "ladder", "grid"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.num_levels < 1:
            raise ValueError("num_levels must be >= 1")
        if not (Decimal("0") < self.quantity_decay <= Decimal("1")):
            raise ValueError("quantity_decay must be in (0, 1]")


@register_strategy("ladder_quoting", "market_making", tags=["market_making", "ladder", "grid"])
class LadderQuotingStrategy(QuotingStrategy):
    """Multi-level ladder quoting with geometric size decay."""

    name = "ladder_quoting"
    Config = LadderQuotingConfig

    def __init__(self, config: LadderQuotingConfig) -> None:
        super().__init__(
            quoting_side="BOTH",
            quoting_quantity=config.base_quantity,
            price_tolerance=config.quote_quantity * Decimal("0.0001") if config.quote_quantity else Decimal("0.1"),
        )
        self.config = config
        self.num_levels = config.num_levels
        self.level_spread_bps = config.level_spread_bps
        self.base_quantity = config.base_quantity
        self.quantity_decay = float(config.quantity_decay)
        self.max_inventory = config.max_total_inventory

        # Track active orders per level
        self._bid_levels: dict[int, Decimal] = {}  # level -> order_id
        self._ask_levels: dict[int, Decimal] = {}
        self._last_mid: Decimal | None = None

    def on_quote(self, quote) -> None:
        """Update ladder quotes based on current mid price."""
        mid = (quote.bid_price + quote.ask_price) / 2

        # Check if we need to rebalance
        if self._last_mid is not None:
            move_bps = abs(mid - self._last_mid) / mid * 10000
            if move_bps < self.config.rebalance_threshold_bps:
                return  # No significant move, keep current ladder

        self._last_mid = mid
        self._rebuild_ladder(mid)

    def _rebuild_ladder(self, mid: Decimal) -> None:
        """Rebuild entire ladder around new mid price."""
        # Cancel all existing orders
        for level in list(self._bid_levels.keys()):
            self._cancel_level("BID", level)
        for level in list(self._ask_levels.keys()):
            self._cancel_level("ASK", level)

        # Calculate current inventory
        current_pos = self.ctx.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")

        # Determine active levels based on inventory
        max_active = min(self.config.max_levels_active, self.num_levels)

        # Build bid ladder (below mid)
        for level in range(1, max_active + 1):
            if float(current_pos) >= float(self.config.max_total_inventory):
                break  # Don't add more bids if long
            spread = mid * (self.config.level_spread_bps * level / Decimal("10000"))
            bid_price = mid - spread
            qty = self._level_quantity(level)
            if qty > 0:
                self._bid_levels[level] = self._place_order("BID", bid_price, qty)

        # Build ask ladder (above mid)
        for level in range(1, max_active + 1):
            if float(current_pos) <= -float(self.config.max_total_inventory):
                break  # Don't add more asks if short
            spread = mid * (self.config.level_spread_bps * level / Decimal("10000"))
            ask_price = mid + spread
            qty = self._level_quantity(level)
            if qty > 0:
                self._ask_levels[level] = self._place_order("ASK", ask_price, qty)

    def _level_quantity(self, level: int) -> Decimal:
        """Calculate quantity for a given level with geometric decay."""
        qty = self.config.base_quantity * Decimal(str(self.quantity_decay ** (level - 1)))
        return max(qty, Decimal("1"))  # Minimum 1 unit

    def _place_order(self, side: str, price: Decimal, qty: Decimal) -> Decimal:
        """Place order and return order ID (simplified)."""
        intent = None
        if side == "BID":
            intent = self.ctx.submit_intent.limit_buy(self.instrument_id, float(qty), float(price))
        else:
            intent = self.ctx.submit_intent.limit_sell(self.instrument_id, float(qty), float(price))
        return intent

    def _cancel_level(self, side: str, level: int) -> None:
        """Cancel order at specific level."""
        # In production, would cancel the specific order ID
        pass

    def on_fill(self, fill) -> None:
        """Update inventory tracking."""
        super().on_fill(fill)