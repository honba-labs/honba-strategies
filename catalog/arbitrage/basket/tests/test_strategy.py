"""Tests for Basket Arbitrage strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.arbitrage import BasketArbitrageStrategy, BasketConfig


def test_basket_arbitrage_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = BasketConfig(
        name="basket",
        symbol="NIFTYBEES",
        etf_symbol="NIFTYBEES",
        etf_exchange="NSE",
        constituents=["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK"],
        min_basis_bps=Decimal("10"),
        rebalance_threshold_bps=Decimal("5"),
    )
    strategy = BasketArbitrageStrategy(config)
    assert strategy.name == "basket"
    assert strategy.config.etf_symbol == "NIFTYBEES"