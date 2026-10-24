"""Tests for Alpha Factor strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.portfolio import AlphaFactorStrategy, AlphaFactorConfig


def test_alpha30_factor_catalog_entry():
    config = AlphaFactorConfig(
        name="alpha30_factor",
        symbol="",
        exchange="NSE",
        top_n=30,
    )
    strategy = AlphaFactorStrategy(config)
    assert strategy.name == "alpha30_factor"
    assert strategy.config.top_n == 30
