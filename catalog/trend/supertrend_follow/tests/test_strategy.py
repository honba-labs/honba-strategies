"""Tests for Supertrend strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.trend import SupertrendConfig, SupertrendStrategy


def test_supertrend_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = SupertrendConfig(
        name="supertrend_follow",
        symbol="RELIANCE",
        exchange="NSE",
        atr_period=10,
        multiplier=Decimal("3.0"),
    )
    strategy = SupertrendStrategy(config)
    assert strategy.name == "supertrend_follow"
    assert strategy.config.atr_period == 10
    assert strategy.config.multiplier == Decimal("3.0")