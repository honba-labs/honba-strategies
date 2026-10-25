"""Supertrend Strategy - catalog entry."""

from honba_strategies.trend import SupertrendConfig, SupertrendStrategy

__all__ = ["SupertrendConfig", "SupertrendStrategy"]

# Alias for registry compatibility
SupertrendStrategyFollow = SupertrendStrategy