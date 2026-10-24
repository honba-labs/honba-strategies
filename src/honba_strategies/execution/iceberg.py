"""Iceberg (Synthetic) Execution Strategy.

Displays small visible quantity while holding hidden balance in local order manager.
Automatically replenishes visible leg upon complete fill with randomized display size.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import SlicingStrategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class IcebergConfig(BaseStrategyConfig):
    """Configuration for Iceberg execution strategy."""

    # Required parameters
    total_quantity: Decimal = Decimal("1000")
    display_size: Decimal = Decimal("100")
    display_variance: Decimal = Decimal("0.2")

    # Optional parameters
    freeze_limit: int = 1800
    min_refill_interval: int = 2
    price_limit: Decimal = Decimal("0.0")
    side: str = "BUY"

    _registry_meta: ClassVar[dict] = {
        "name": "iceberg",
        "category": "execution",
        "description": "Synthetic iceberg order with hidden reserve and randomized display",
        "tags": ["execution", "slicing", "iceberg"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.display_size > self.freeze_limit:
            self.display_size = Decimal(str(self.freeze_limit))
        if not (Decimal("0") <= self.display_variance <= Decimal("1")):
            raise ValueError("display_variance must be in [0, 1]")


@register_strategy("iceberg", "execution", tags=["execution", "slicing", "iceberg"])
class IcebergStrategy(SlicingStrategy):
    """Synthetic Iceberg execution strategy with hidden reserve."""

    name = "iceberg"
    Config = IcebergConfig

    def __init__(self, config: IcebergConfig) -> None:
        super().__init__(
            total_quantity=config.total_quantity,
            slice_size=config.display_size,  # Base display size
            side=config.side,
        )
        self.instrument_id = config.instrument_id
        self.freeze_limit = config.freeze_limit
        self.display_size = config.display_size
        # Cap display_size at freeze_limit
        if self.display_size > self.freeze_limit:
            self.display_size = Decimal(str(self.freeze_limit))
        self.display_variance = float(config.display_variance)
        self.min_refill_interval = config.min_refill_interval
        self.price_limit = config.price_limit if config.price_limit > 0 else None

        self._hidden_reserve = config.total_quantity
        self._active_display: Decimal | None = None
        self._bars_since_fill = 0

    def _compute_display_qty(self) -> Decimal:
        """Compute randomized display quantity within variance bounds."""
        if self.display_variance <= 0:
            return min(self.display_size, Decimal(str(self.freeze_limit)))

        variance = self.display_size * Decimal(str(self.display_variance))
        min_disp = max(Decimal(1), self.display_size - variance)
        max_disp = min(self.display_size + variance, Decimal(str(self.freeze_limit)))
        disp = min_disp + (max_disp - min_disp) * Decimal(str(random.random()))
        return disp.quantize(Decimal('1'))

    def _get_price(self, bar) -> Decimal | None:
        """Get limit price if price_limit is set, else None for market."""
        if self.price_limit is None or self.price_limit <= 0:
            return None
        mid = (bar.high + bar.low) / 2
        if self.side == "BUY":
            return mid + self.price_limit
        else:
            return mid - self.price_limit

    def on_bar(self, bar) -> None:
        self._bars_since_fill += 1

        # Check if active display was filled
        if self._active_display is not None and self._active_display <= 0:
            self._active_display = None

        # Replenish visible leg if needed
        if (
            (self._active_display is None or self._active_display <= 0)
            and self._hidden_reserve > 0
            and self._bars_since_fill >= self.min_refill_interval
        ):
            self._replenish(bar)

    def _replenish(self, bar) -> None:
        if self._hidden_reserve <= 0:
            return

        display_qty = self._compute_display_qty()
        actual_qty = min(display_qty, self._hidden_reserve, Decimal(str(self.freeze_limit)))

        price = self._get_price(bar)
        if actual_qty > 0:
            if price is not None:
                self.ctx.submit_intent(
                    self.instrument_id,
                    float(actual_qty),
                    float(price),
                    self.side == "BUY",
                )
            else:
                self.execute_slice(self.instrument_id, price=None)

            self._active_display = actual_qty
            self._bars_since_fill = 0

    def on_fill(self, fill) -> None:
        super().on_fill(fill)
        self._bars_since_fill = 0
        filled = Decimal(str(fill.quantity))
        self._hidden_reserve = max(Decimal(0), self._hidden_reserve - filled)
        if self._active_display is not None:
            self._active_display = max(Decimal(0), self._active_display - filled)