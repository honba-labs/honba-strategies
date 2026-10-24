"""VWAP (Volume-Weighted Average Price) Execution Strategy.

Dynamic slice sizing proportional to historical exchange intraday volume curve
(NSE 09:15-15:30 profile). Real-time pace adjustment based on accumulated volume.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import SlicingStrategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class VwapConfig(BaseStrategyConfig):
    """Configuration for VWAP execution strategy."""

    # Required parameters
    total_quantity: Decimal = Decimal("1000")
    slice_size: Decimal = Decimal("100")
    participation_rate: Decimal = Decimal("0.1")

    # Optional parameters
    freeze_limit: int = 1800
    volume_profile_path: str = ""
    side: str = "BUY"

    _registry_meta: ClassVar[dict] = {
        "name": "vwap",
        "category": "execution",
        "description": "VWAP execution with volume-profile-based dynamic slice sizing",
        "tags": ["execution", "slicing", "vwap", "volume"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.slice_size > self.freeze_limit:
            self.slice_size = Decimal(str(self.freeze_limit))
        if not (Decimal("0") < self.participation_rate <= Decimal("1")):
            raise ValueError("participation_rate must be in (0, 1]")
        if self.total_quantity <= 0:
            raise ValueError("total_quantity must be positive")


@register_strategy("vwap", "execution", tags=["execution", "slicing", "vwap", "volume"])
class VwapStrategy(SlicingStrategy):
    """VWAP execution strategy using historical volume profile for slice sizing."""

    name = "vwap"
    Config = VwapConfig

    def __init__(self, config: VwapConfig) -> None:
        super().__init__(
            total_quantity=config.total_quantity,
            slice_size=config.slice_size,
            side=config.side,
        )
        self.instrument_id = config.instrument_id
        self.participation_rate = float(config.participation_rate)
        self.freeze_limit = config.freeze_limit
        self.volume_profile_path = config.volume_profile_path

        # Load historical volume profile (minute-of-day -> relative volume)
        self.volume_profile = self._load_volume_profile()
        self._accumulated_volume = Decimal(0)
        self._target_volume = Decimal(0)
        self._current_minute = -1

    def _load_volume_profile(self) -> dict[int, float]:
        """Load historical volume profile. Returns minute-of-day -> relative volume factor."""
        # Default NSE volume profile (U-shaped: high at open/close, low midday)
        return {
            915: 1.5, 916: 1.3, 917: 1.2, 918: 1.1, 919: 1.0,
            920: 0.9, 930: 0.8, 945: 0.7, 1000: 0.7, 1030: 0.6,
            1100: 0.6, 1130: 0.6, 1200: 0.6, 1230: 0.6, 1300: 0.6,
            1330: 0.7, 1400: 0.8, 1430: 0.9, 1445: 1.0, 1500: 1.2,
            1515: 1.5, 1530: 2.0
        }

    def _minute_of_day(self, bar) -> int:
        """Extract minute-of-day as HHMM integer from bar timestamp."""
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour * 100 + bar.ts.minute
        return 915  # Default to market open

    def _get_volume_factor(self, minute: int) -> float:
        """Get volume factor for current minute, interpolating if needed."""
        minutes = sorted(self.volume_profile.keys())
        if minute <= minutes[0]:
            return self.volume_profile[minutes[0]]
        if minute >= minutes[-1]:
            return self.volume_profile[minutes[-1]]
        # Linear interpolation
        for i in range(len(minutes) - 1):
            if minutes[i] <= minute < minutes[i + 1]:
                m1, m2 = minutes[i], minutes[i + 1]
                v1, v2 = self.volume_profile[m1], self.volume_profile[m2]
                t = (minute - m1) / (m2 - m1)
                return v1 + t * (v2 - v1)
        return 1.0

    def on_bar(self, bar) -> None:
        minute = self._minute_of_day(bar)
        if minute != self._current_minute:
            self._current_minute = minute
            # Update target volume based on volume profile
            vol_factor = self._get_volume_factor(minute)
            expected_vol = Decimal(str(bar.volume)) * Decimal(str(vol_factor))
            self._target_volume += expected_vol * Decimal(str(self.participation_rate))

        # Check if we've accumulated enough volume to dispatch a slice
        self._accumulated_volume += Decimal(str(bar.volume))
        if self._accumulated_volume >= self._target_volume and self.remaining_to_dispatch > 0:
            self._dispatch_slice(bar)

    def _dispatch_slice(self, _bar) -> None:
        if self.remaining_to_dispatch <= 0:
            return

        # Slice size scales with volume factor
        vol_factor = self._get_volume_factor(self._current_minute)
        adjusted_slice = Decimal(str(self.slice_size)) * Decimal(str(max(0.1, vol_factor)))
        adjusted_slice = min(adjusted_slice, Decimal(str(self.freeze_limit)))

        qty = min(adjusted_slice, self.remaining_to_dispatch)
        if qty > 0:
            self.execute_slice(self.instrument_id, price=None)
            self._target_volume = Decimal(0)
            self._accumulated_volume = Decimal(0)