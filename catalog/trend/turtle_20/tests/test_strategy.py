"""Tests for Turtle Trading strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.trend import TurtleConfig, TurtleStrategy


def test_turtle_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = TurtleConfig(
        name="turtle_20",
        symbol="RELIANCE",
        exchange="NSE",
        system=1,
        atr_period=20,
        atr_multiplier=Decimal("2.0"),
        pyramid_threshold=Decimal("0.5"),
        max_units=4,
    )
    strategy = TurtleStrategy(config)
    assert strategy.name == "turtle_20"
    assert strategy.config.system == 1
    assert strategy.channel_period == 20
    assert strategy.atr_multiplier == Decimal("2.0")