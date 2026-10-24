"""Tests for Ladder Quoting strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.market_making import LadderQuotingStrategy, LadderQuotingConfig


def test_ladder_quoting_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = LadderQuotingConfig(
        name="ladder_quoting",
        symbol="RELIANCE",
        exchange="NSE",
        num_levels=5,
        level_spread_bps=Decimal("5"),
        base_quantity=Decimal("100"),
    )
    strategy = LadderQuotingStrategy(config)
    assert strategy.name == "ladder_quoting"
    assert strategy.config.num_levels == 5
    assert strategy.config.level_spread_bps == Decimal("5")
    assert strategy.config.base_quantity == Decimal("100")