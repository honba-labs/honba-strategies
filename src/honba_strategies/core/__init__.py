"""Core SDK foundation: configuration, error hierarchy, and strategy registry."""

from honba_strategies.core.config import BaseStrategyConfig, StrategyConfig
from honba_strategies.core.errors import (
    ConfigValidationError,
    DataError,
    ExecutionError,
    HonbaStrategyError,
    RegimeNotSupportedError,
    RiskLimitExceededError,
)
from honba_strategies.core.registry import (
    StrategyRegistry,
    create_strategy,
    get_strategy,
    get_strategy_class,
    list_categories,
    list_strategies,
    register_strategy,
)

__all__ = [
    "BaseStrategyConfig",
    "ConfigValidationError",
    "DataError",
    "ExecutionError",
    # Errors
    "HonbaStrategyError",
    "RegimeNotSupportedError",
    "RiskLimitExceededError",
    # Config
    "StrategyConfig",
    # Registry
    "StrategyRegistry",
    "create_strategy",
    "get_strategy",
    "get_strategy_class",
    "list_categories",
    "list_strategies",
    "register_strategy",
]