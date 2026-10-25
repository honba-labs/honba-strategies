"""Tests for Spread Quoting strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.market_making import SpreadQuotingConfig, SpreadQuotingStrategy


def test_spread_quoting_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = SpreadQuotingConfig(
        name="spread_quoting",
        symbol="RELIANCE",
        exchange="NSE",
        spread_bps=Decimal("10"),
        quote_quantity=Decimal("100"),
        obi_threshold=Decimal("0.3"),
    )
    strategy = SpreadQuotingStrategy(config)
    assert strategy.name == "spread_quoting"
    assert strategy.config.spread_bps == Decimal("10")
    assert strategy.config.quote_quantity == Decimal("100")
    assert strategy.config.obi_threshold == Decimal("0.3")