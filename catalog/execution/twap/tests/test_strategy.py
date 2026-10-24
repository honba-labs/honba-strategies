"""Tests for TWAP execution strategy (catalog entry)."""

from honba_strategies.execution import TwapConfig, TwapStrategy


def test_twap_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = TwapConfig(
        name="twap",
        symbol="NIFTY50",
        exchange="NSE",
        total_quantity=1000,
        slice_size=100,
    )
    strategy = TwapStrategy(config)
    assert strategy.name == "twap"
