"""Tests for Avellaneda-Stoikov strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.market_making import AvellanedaStoikovStrategy, AvellanedaStoikovConfig


def test_avellaneda_stoikov_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = AvellanedaStoikovConfig(
        name="avellaneda_stoikov",
        symbol="RELIANCE",
        exchange="NSE",
        gamma=Decimal("0.1"),
        sigma=Decimal("0.02"),
        kappa=Decimal("1.5"),
        quote_quantity=Decimal("100"),
    )
    strategy = AvellanedaStoikovStrategy(config)
    assert strategy.name == "avellaneda_stoikov"
    assert strategy.config.gamma == Decimal("0.1")
    assert strategy.config.sigma == Decimal("0.02")
    assert strategy.config.kappa == Decimal("1.5")