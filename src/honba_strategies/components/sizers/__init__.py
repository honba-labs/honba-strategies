"""Position Sizing Engines - First-Class Dynamic Position Sizing.

This module provides reusable, composable position sizing engines that can be
plugged into any strategy or chained declaratively via step.toml manifests.

Available Sizers:
- FixedFractionalSizer: Risk % of equity per trade vs stop-loss distance
- AtrVolatilitySizer: Inverse volatility allocation based on ATR
- KellySizer: Kelly criterion optimal fraction with fractional damping
- EqualRiskSizer: Equal risk contribution / risk parity across signals
- FixedNotionalSizer: Fixed cash notional with lot-size rounding

All sizers use exact 128-bit Decimal arithmetic and enforce exchange constraints
(lot size discretization, freeze limits, max position caps).
"""

from __future__ import annotations

from honba_strategies.components.sizers.base import (
    BasePositionSizer,
    PositionSizingResult,
    Signal,
    SizingContext,
)
from honba_strategies.components.sizers.equal_risk import EqualRiskSizer
from honba_strategies.components.sizers.fixed_fractional import FixedFractionalSizer
from honba_strategies.components.sizers.fixed_notional import FixedNotionalSizer
from honba_strategies.components.sizers.kelly import KellySizer
from honba_strategies.components.sizers.volatility import AtrVolatilitySizer

__all__ = [
    "AtrVolatilitySizer",
    "BasePositionSizer",
    "EqualRiskSizer",
    "FixedFractionalSizer",
    "FixedNotionalSizer",
    "KellySizer",
    "PositionSizingResult",
    "Signal",
    "SizingContext",
]

# Sizer registry for discovery
_SIZER_REGISTRY: dict[str, type[BasePositionSizer]] = {
    "fixed_fractional": FixedFractionalSizer,
    "atr_volatility": AtrVolatilitySizer,
    "kelly_criterion": KellySizer,
    "equal_risk": EqualRiskSizer,
    "fixed_notional": FixedNotionalSizer,
}


def get_sizer(name: str) -> type[BasePositionSizer]:
    """Get sizer class by registry name."""
    if name not in _SIZER_REGISTRY:
        raise KeyError(f"Unknown sizer: {name}. Available: {list(_SIZER_REGISTRY.keys())}")
    return _SIZER_REGISTRY[name]


def list_sizers() -> list[str]:
    """List all registered sizer names."""
    return list(_SIZER_REGISTRY.keys())