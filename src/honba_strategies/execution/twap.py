"""TWAP (Time-Weighted Average Price) Execution Strategy.

Divides a large parent order into N equal slices distributed evenly across
a specified execution duration. Adds randomized jitter to avoid exchange
algorithm detection. Enforces SEBI single-order freeze limit slicing.
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
class TwapConfig(BaseStrategyConfig):
    """Configuration for TWAP execution strategy."""

    # Required parameters
    total_quantity: Decimal = Decimal("1000")
    slice_size: Decimal = Decimal("100")
    duration_minutes: int = 60

    # Optional parameters
    jitter_seconds: int = 5
    freeze_limit: int = 1800
    side: str = "BUY"

    # Strategy metadata (ClassVar to avoid dataclass field)
    _registry_meta: ClassVar[dict] = {
        "name": "twap",
        "category": "execution",
        "description": "TWAP execution with time-based slicing and randomized jitter",
        "tags": ["execution", "slicing", "twap"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.slice_size > self.freeze_limit:
            self.slice_size = Decimal(str(self.freeze_limit))
        if self.total_quantity <= 0:
            raise ValueError("total_quantity must be positive")
        if self.slice_size <= 0:
            raise ValueError("slice_size must be positive")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")


@register_strategy("twap", "execution", tags=["execution", "slicing", "twap"])
class TwapStrategy(SlicingStrategy):
    """TWAP execution strategy dividing parent order into time-based slices."""

    name = "twap"
    Config = TwapConfig

    def __init__(self, config: TwapConfig) -> None:
        super().__init__(
            total_quantity=config.total_quantity,
            slice_size=config.slice_size,
            side=config.side,
        )
        self.instrument_id = config.instrument_id
        self.duration_minutes = config.duration_minutes
        self.jitter_seconds = config.jitter_seconds
        self.freeze_limit = config.freeze_limit

        # Compute interval between slices (in bars)
        self.num_slices = max(1, int(self.total_quantity / self.slice_size))
        self.interval_bars = self.duration_minutes // max(1, self.num_slices - 1) if self.num_slices > 1 else 0
        self._next_slice_bar: int | None = None
        self._started = False

    def on_bar(self, bar) -> None:
        bar_idx = int(bar.ts) if hasattr(bar, 'ts') else 0
        if not self._started:
            self._started = True
            self._next_slice_bar = bar_idx
            # Dispatch first slice immediately
            self._dispatch_slice(bar)
            return

        if self._next_slice_bar is not None and bar_idx >= self._next_slice_bar:
            self._dispatch_slice(bar)

    def _dispatch_slice(self, _bar) -> None:
        if self.remaining_to_dispatch <= 0:
            return

        # Apply jitter to next slice bar
        if self._next_slice_bar is not None and self.num_slices > 1:
            jitter = random.randint(0, max(0, self.jitter_seconds))
            self._next_slice_bar += self.interval_bars + jitter

        qty = self.next_slice_quantity()
        if qty > self.freeze_limit:
            qty = Decimal(str(self.freeze_limit))

        if qty > 0:
            self.execute_slice(self.instrument_id, price=None)