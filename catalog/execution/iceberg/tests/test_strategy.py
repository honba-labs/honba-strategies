"""Tests for Iceberg execution strategy (catalog entry)."""

from honba_strategies.execution import IcebergConfig, IcebergStrategy


def test_iceberg_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = IcebergConfig(
        name="iceberg",
        symbol="NIFTY50",
        exchange="NSE",
        total_quantity=1000,
        display_size=100,
    )
    strategy = IcebergStrategy(config)
    assert strategy.name == "iceberg"
