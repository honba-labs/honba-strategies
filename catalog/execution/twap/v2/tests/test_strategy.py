"""Tests for TWAP execution strategy v2 (catalog entry)."""

from catalog.execution.twap.v2.strategy import TwapStrategy
from honba_strategies.execution import TwapConfig


def test_twap_v2_catalog_entry():
    """Verify the v2 catalog entry can be imported and instantiated."""
    config = TwapConfig(
        name="twap",
        symbol="NIFTY50",
        exchange="NSE",
        total_quantity=1000,
        slice_size=100,
    )
    strategy = TwapStrategy(config)
    assert strategy.name == "twap"
    assert getattr(strategy, "__strategy_api_version__", None) == "2.0.0"
