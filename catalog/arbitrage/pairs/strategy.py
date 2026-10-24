"""Pairs Trading Strategy - catalog entry."""

from honba_strategies.arbitrage import PairsTradingStrategy, PairsConfig

__all__ = ["PairsTradingStrategy", "PairsConfig"]

# Alias for registry compatibility
PairsStrategy = PairsTradingStrategy