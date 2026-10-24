"""POV (Percentage of Volume) Execution Strategy.

Participates at a target rate (e.g., 5% or 10% of market volume).
Dynamically speeds up during volume spikes and pauses during liquidity droughts.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import SlicingStrategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class PovConfig(BaseStrategyConfig):
    """Configuration for POV execution strategy."""

    # Required parameters
    total_quantity: Decimal = Decimal("1000")
    target_rate: Decimal = Decimal("0.05")
    max_slice_size: Decimal = Decimal("200")
    min_slice_size: Decimal = Decimal("10")

    # Optional parameters
    freeze_limit: int = 1800
    volume_window: int = 5
    side: str = "BUY"

    _registry_meta: ClassVar[dict] = {
        "name": "pov",
        "category": "execution",
        "description": "POV execution participating at target rate of market volume",
        "tags": ["execution", "slicing", "pov", "volume"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.max_slice_size > self.freeze_limit:
            self.max_slice_size = Decimal(str(self.freeze_limit))
        if not (Decimal("0") < self.target_rate <= Decimal("1")):
            raise ValueError("target_rate must be in (0, 1]")
        if self.min_slice_size <= 0:
            raise ValueError("min_slice_size must be positive")


@register_strategy("pov", "execution", tags=["execution", "slicing", "pov", "volume"])
class PovStrategy(SlicingStrategy):
    """POV execution strategy participating at target rate of market volume."""

    name = "pov"
    Config = PovConfig

    def __init__(self, config: PovConfig) -> None:
        super().__init__(
            total_quantity=config.total_quantity,
            slice_size=config.max_slice_size,  # Use max as base
            side=config.side,
        )
        self.instrument_id = config.instrument_id
        self.target_rate = float(config.target_rate)
        self.max_slice_size = config.max_slice_size
        self.min_slice_size = config.min_slice_size
        self.freeze_limit = config.freeze_limit
        self.volume_window = config.volume_window

        # Cap max_slice_size at freeze_limit
        if self.max_slice_size > self.freeze_limit:
            self.max_slice_size = Decimal(str(self.freeze_limit))

        # Rolling volume tracking
        self._recent_volumes: list[Decimal] = []
        self._accumulated_participation = Decimal(0)

    def _compute_dynamic_slice(self, current_volume: Decimal) -> Decimal:
        """Compute slice size based on current market volume and target rate."""
        self._recent_volumes.append(current_volume)
        if len(self._recent_volumes) > self.volume_window:
            self._recent_volumes.pop(0)

        if not self._recent_volumes:
            return self.min_slice_size

        avg_volume = sum(self._recent_volumes) / len(self._recent_volumes)
        target_volume = avg_volume * Decimal(str(self.target_rate))

        # Clamp to min/max bounds and freeze limit
        slice_size = min(max(target_volume, self.min_slice_size), self.max_slice_size)
        slice_size = min(slice_size, Decimal(str(self.freeze_limit)))
        return slice_size

    def on_bar(self, bar) -> None:
        current_volume = Decimal(str(bar.volume))
        if current_volume <= 0:
            return

        # Update accumulated participation
        self._accumulated_participation += current_volume * Decimal(str(self.target_rate))

        # Dispatch slice when accumulated participation exceeds slice size
        if self._accumulated_participation >= self.min_slice_size and self.remaining_to_dispatch > 0:
            dynamic_slice = self._compute_dynamic_slice(current_volume)
            qty = min(dynamic_slice, self.remaining_to_dispatch)
            if qty > 0:
                self.execute_slice(self.instrument_id, price=None)
                self._accumulated_participation = Decimal(0)