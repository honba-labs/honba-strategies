"""Tests for VWAP Band Reversion strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.mean_reversion import VwapBandConfig, VwapBandReversionStrategy


def test_vwap_bands_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = VwapBandConfig(
        name="vwap_bands",
        symbol="RELIANCE",
        exchange="NSE",
        std_dev_mult=Decimal("2.5"),
        entry_cutoff="15:00",
        square_off="15:20",
    )
    strategy = VwapBandReversionStrategy(config)
    assert strategy.name == "vwap_bands"
    assert strategy.config.std_dev_mult == Decimal("2.5")
    assert strategy.config.entry_cutoff == "15:00"
    assert strategy.config.square_off == "15:20"