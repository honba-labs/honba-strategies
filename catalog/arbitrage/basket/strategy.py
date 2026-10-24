"""Basket Arbitrage Strategy - catalog entry."""

from honba_strategies.arbitrage import BasketArbitrageStrategy, BasketConfig

__all__ = ["BasketArbitrageStrategy", "BasketConfig"]

# Alias for registry compatibility
BasketStrategy = BasketArbitrageStrategy