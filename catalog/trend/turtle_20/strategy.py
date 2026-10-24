"""Turtle Trading System - catalog entry."""

from honba_strategies.trend import TurtleStrategy, TurtleConfig

__all__ = ["TurtleStrategy", "TurtleConfig"]

# Alias for registry compatibility
TurtleStrategy20 = TurtleStrategy