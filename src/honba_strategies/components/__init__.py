"""Composable Strategy Building Blocks.

This package provides reusable, modular components for building trading systems:
- signals: Alpha signal generators (cointegration, OU, Donchian, etc.)
- sizers: Dynamic position sizing engines (fixed fractional, ATR, Kelly, ERC, fixed notional)
- risk: Indian regulatory & microstructure risk guards (SEBI Algo ID, OTR, MIS square-off, circuit bands)
"""

from __future__ import annotations

from honba_strategies.components.risk import (
    BaseRiskGuard,
    CircuitBandGuard,
    DrawdownHaltGuard,
    MaxPositionGuard,
    MisSquareOffGuard,
    OtrThrottleGuard,
    RiskCheckResult,
    SebiAlgoIdGuard,
)
from honba_strategies.components.signals import (
    CointegrationSignal,
    DonchianBreakoutSignal,
    OrnsteinUhlenbeckSignal,
)
from honba_strategies.components.sizers import (
    AtrVolatilitySizer,
    BasePositionSizer,
    EqualRiskSizer,
    FixedFractionalSizer,
    FixedNotionalSizer,
    KellySizer,
    PositionSizingResult,
    Signal,
    SizingContext,
    get_sizer,
    list_sizers,
)

__all__ = [
    "AtrVolatilitySizer",
    # Sizers
    "BasePositionSizer",
    # Risk Guards
    "BaseRiskGuard",
    "CircuitBandGuard",
    # Signals
    "CointegrationSignal",
    "DonchianBreakoutSignal",
    "DrawdownHaltGuard",
    "EqualRiskSizer",
    "FixedFractionalSizer",
    "FixedNotionalSizer",
    "KellySizer",
    "MaxPositionGuard",
    "MisSquareOffGuard",
    "OrnsteinUhlenbeckSignal",
    "OtrThrottleGuard",
    "PositionSizingResult",
    "RiskCheckResult",
    "SebiAlgoIdGuard",
    "Signal",
    "SizingContext",
    "get_sizer",
    "list_sizers",
]