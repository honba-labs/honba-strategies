"""Tests for Cash-and-Carry strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.arbitrage import CashAndCarryConfig, CashAndCarryStrategy


def test_cash_and_carry_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = CashAndCarryConfig(
        name="cash_and_carry",
        symbol="RELIANCE",
        spot_symbol="RELIANCE",
        futures_symbol="RELIANCE",
        futures_expiry="2026-12-25",
        min_basis_bps=Decimal("50"),
        lot_size=250,
    )
    strategy = CashAndCarryStrategy(config)
    assert strategy.name == "cash_and_carry"
    assert strategy.config.spot_symbol == "RELIANCE"
    assert strategy.config.futures_symbol == "RELIANCE"