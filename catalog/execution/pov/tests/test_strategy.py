"""Tests for POV execution strategy (catalog entry)."""

from honba_strategies.execution import PovConfig, PovStrategy


def test_pov_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = PovConfig(
        name="pov",
        symbol="NIFTY50",
        exchange="NSE",
        total_quantity=1000,
        target_rate=0.1,
    )
    strategy = PovStrategy(config)
    assert strategy.name == "pov"
