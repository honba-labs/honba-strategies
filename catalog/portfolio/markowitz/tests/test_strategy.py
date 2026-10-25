"""Tests for Markowitz strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.portfolio import MarkowitzConfig, MarkowitzStrategy


def test_markowitz_catalog_entry():
    config = MarkowitzConfig(
        name="markowitz",
        symbol="",
        exchange="NSE",
        max_weight=Decimal("0.20"),
    )
    strategy = MarkowitzStrategy(config)
    assert strategy.name == "markowitz"
    assert strategy.config.max_weight == Decimal("0.20")
