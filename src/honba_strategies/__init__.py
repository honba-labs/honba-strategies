"""honba-strategies: Production quantitative strategy SDK for Honba platform.

This package provides battle-tested algorithmic trading strategies,
institutional execution algorithms, statistical arbitrage models,
high-frequency quoting engines, and dynamic portfolio rebalancers
ported from StockSharp and modernized for Indian financial markets.
"""

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
    OtrThrottleGuard,
    OrnsteinUhlenbeckSignal,
    PositionSizingResult,
    RiskCheckResult,
    SebiAlgoIdGuard,
    Signal,
    SizingContext,
    get_sizer,
    list_sizers,
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
    # Core
    "ConfigValidationError",
    "HonbaStrategyError",
    "RiskLimitExceededError",
    "StrategyConfig",
    "StrategyRegistry",
    "create_strategy",
    "get_strategy",
    "list_categories",
    "list_strategies",
    "register_strategy",
    # Execution
    "TwapConfig",
    "TwapStrategy",
    "VwapConfig",
    "VwapStrategy",
    "PovConfig",
    "PovStrategy",
    "IcebergConfig",
    "IcebergStrategy",
    # Options
    "ShortStraddleConfig",
    "ShortStraddleStrategy",
    "IronCondorConfig",
    "IronCondorStrategy",
    "CoveredCallConfig",
    "CoveredCallStrategy",
    "CalendarSpreadConfig",
    "CalendarSpreadStrategy",
    # Components - Sizers
    "BasePositionSizer",
    "PositionSizingResult",
    "Signal",
    "SizingContext",
    "FixedFractionalSizer",
    "AtrVolatilitySizer",
    "KellySizer",
    "EqualRiskSizer",
    "FixedNotionalSizer",
    "get_sizer",
    "list_sizers",
    # Components - Signals
    "CointegrationSignal",
    "OrnsteinUhlenbeckSignal",
    "DonchianBreakoutSignal",
    # Components - Risk Guards
    "BaseRiskGuard",
    "RiskCheckResult",
    "SebiAlgoIdGuard",
    "OtrThrottleGuard",
    "MisSquareOffGuard",
    "CircuitBandGuard",
    "MaxPositionGuard",
    "DrawdownHaltGuard",
]