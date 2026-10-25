"""honba-strategies: Production quantitative strategy SDK for Honba platform.

This package provides battle-tested algorithmic trading strategies,
institutional execution algorithms, statistical arbitrage models,
high-frequency quoting engines, and dynamic portfolio rebalancers
ported from StockSharp and modernized for Indian financial markets.
"""

from honba_strategies.components import (
    AtrVolatilitySizer,
    BasePositionSizer,
    BaseRiskGuard,
    CircuitBandGuard,
    CointegrationSignal,
    DonchianBreakoutSignal,
    DrawdownHaltGuard,
    EqualRiskSizer,
    FixedFractionalSizer,
    FixedNotionalSizer,
    KellySizer,
    MaxPositionGuard,
    MisSquareOffGuard,
    OrnsteinUhlenbeckSignal,
    OtrThrottleGuard,
    PositionSizingResult,
    RiskCheckResult,
    SebiAlgoIdGuard,
    Signal,
    SizingContext,
    get_sizer,
    list_sizers,
)
from honba_strategies.core import (
    ConfigValidationError,
    HonbaStrategyError,
    RiskLimitExceededError,
    StrategyConfig,
    StrategyRegistry,
    create_strategy,
    get_strategy,
    list_categories,
    list_strategies,
    register_strategy,
)
from honba_strategies.execution import (
    IcebergConfig,
    IcebergStrategy,
    PovConfig,
    PovStrategy,
    TwapConfig,
    TwapStrategy,
    VwapConfig,
    VwapStrategy,
)
from honba_strategies.options import (
    CalendarSpreadConfig,
    CalendarSpreadStrategy,
    CoveredCallConfig,
    CoveredCallStrategy,
    IronCondorConfig,
    IronCondorStrategy,
    ShortStraddleConfig,
    ShortStraddleStrategy,
)

__version__ = "0.1.0"

__all__ = [
    "AtrVolatilitySizer",
    # Components - Sizers
    "BasePositionSizer",
    # Components - Risk Guards
    "BaseRiskGuard",
    "CalendarSpreadConfig",
    "CalendarSpreadStrategy",
    "CircuitBandGuard",
    # Components - Signals
    "CointegrationSignal",
    # Core
    "ConfigValidationError",
    "CoveredCallConfig",
    "CoveredCallStrategy",
    "DonchianBreakoutSignal",
    "DrawdownHaltGuard",
    "EqualRiskSizer",
    "FixedFractionalSizer",
    "FixedNotionalSizer",
    "HonbaStrategyError",
    "IcebergConfig",
    "IcebergStrategy",
    "IronCondorConfig",
    "IronCondorStrategy",
    "KellySizer",
    "MaxPositionGuard",
    "MisSquareOffGuard",
    "OrnsteinUhlenbeckSignal",
    "OtrThrottleGuard",
    "PositionSizingResult",
    "PovConfig",
    "PovStrategy",
    "RiskCheckResult",
    "RiskLimitExceededError",
    "SebiAlgoIdGuard",
    # Options
    "ShortStraddleConfig",
    "ShortStraddleStrategy",
    "Signal",
    "SizingContext",
    "StrategyConfig",
    "StrategyRegistry",
    # Execution
    "TwapConfig",
    "TwapStrategy",
    "VwapConfig",
    "VwapStrategy",
    "create_strategy",
    "get_sizer",
    "get_strategy",
    "list_categories",
    "list_sizers",
    "list_strategies",
    "register_strategy",
]