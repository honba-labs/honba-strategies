"""Supertrend Strategy - catalog entry."""

from honba_strategies.trend import SupertrendStrategy, SupertrendConfig

__all__ = ["SupertrendStrategy", "SupertrendConfig"]

# Alias for registry compatibility
SupertrendStrategyFollow = SupertrendStrategy