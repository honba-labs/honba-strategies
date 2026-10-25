"""Trend Following & Breakout Strategies (StockSharp Port).

All trend strategies inherit from honba.strategies.base.Strategy
and integrate SEBI freeze limit compliance, exact Decimal arithmetic,
and declarative catalog manifests.
"""

from honba_strategies.trend.kama import KamaConfig, KamaCrossoverStrategy
from honba_strategies.trend.supertrend import SupertrendConfig, SupertrendStrategy
from honba_strategies.trend.turtle import TurtleConfig, TurtleStrategy

__all__ = [
    "KamaConfig",
    "KamaCrossoverStrategy",
    "SupertrendConfig",
    "SupertrendStrategy",
    "TurtleConfig",
    "TurtleStrategy",
]