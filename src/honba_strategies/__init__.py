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

__version__ = "0.1.0"

__all__ = [
    "ConfigValidationError",
    "HonbaStrategyError",
    "IcebergConfig",
    "IcebergStrategy",
    "PovConfig",
    "PovStrategy",
    "RiskLimitExceededError",
    # Core
    "StrategyConfig",
    "StrategyRegistry",
    "TwapConfig",
    # Execution
    "TwapStrategy",
    "VwapConfig",
    "VwapStrategy",
    "create_strategy",
    "get_strategy",
    "list_categories",
    "list_strategies",
    "register_strategy",
]