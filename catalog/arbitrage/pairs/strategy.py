"""Pairs Trading Strategy - catalog entry."""

from honba_strategies.arbitrage import PairsConfig, PairsTradingStrategy

__all__ = ["PairsConfig", "PairsTradingStrategy"]

# Alias for registry compatibility
PairsStrategy = PairsTradingStrategy