"""Tests for Equal Weight Rebalancer strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.portfolio import EqualWeightRebalancer, EqualWeightConfig


def test_equal_weight_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = EqualWeightConfig(
        name="equal_weight",
        symbol="",
        exchange="NSE",
        drift_threshold=Decimal("0.05"),
        max_positions=10,
    )
    strategy = EqualWeightRebalancer(config)
    assert strategy.name == "equal_weight"
    assert strategy.config.drift_threshold == Decimal("0.05")
    assert strategy.config.max_positions == 10
