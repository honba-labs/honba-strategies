"""Turtle Trading System - catalog entry."""

from honba_strategies.trend import TurtleConfig, TurtleStrategy

__all__ = ["TurtleConfig", "TurtleStrategy"]

# Alias for registry compatibility
TurtleStrategy20 = TurtleStrategy