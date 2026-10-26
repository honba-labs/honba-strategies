"""Tests for TWAP execution strategy v1 (catalog entry)."""

from catalog.execution.twap.v1.strategy import TwapStrategy
from honba_strategies.execution import TwapConfig


def test_twap_v1_catalog_entry():
    """Verify the v1 catalog entry can be imported and instantiated."""
    config = TwapConfig(
        name="twap",
        symbol="NIFTY50",
        exchange="NSE",
        total_quantity=1000,
        slice_size=100,
    )
    strategy = TwapStrategy(config)
    assert strategy.name == "twap"
    assert getattr(strategy, "__strategy_api_version__", None) == "1.0.0"
