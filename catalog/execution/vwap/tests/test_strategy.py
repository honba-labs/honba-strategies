"""Tests for VWAP execution strategy (catalog entry)."""

from honba_strategies.execution import VwapConfig, VwapStrategy


def test_vwap_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = VwapConfig(
        name="vwap",
        symbol="NIFTY50",
        exchange="NSE",
        total_quantity=1000,
        slice_size=100,
    )
    strategy = VwapStrategy(config)
    assert strategy.name == "vwap"
