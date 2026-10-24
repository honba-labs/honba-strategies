"""Trend Following & Breakout Strategies (StockSharp Port).

All trend strategies inherit from honba.strategies.base.Strategy
and integrate SEBI freeze limit compliance, exact Decimal arithmetic,
and declarative catalog manifests.
"""

from honba_strategies.trend.turtle import TurtleStrategy, TurtleConfig
from honba_strategies.trend.kama import KamaCrossoverStrategy, KamaConfig
from honba_strategies.trend.supertrend import SupertrendStrategy, SupertrendConfig

__all__ = [
    "TurtleStrategy",
    "TurtleConfig",
    "KamaCrossoverStrategy",
    "KamaConfig",
    "SupertrendStrategy",
    "SupertrendConfig",
]