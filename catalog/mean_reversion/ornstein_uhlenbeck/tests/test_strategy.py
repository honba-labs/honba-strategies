"""Tests for OU Mean Reversion strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.mean_reversion import OuMeanReversionStrategy, OuConfig


def test_ou_mean_reversion_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = OuConfig(
        name="ornstein_uhlenbeck",
        symbol="RELIANCE",
        exchange="NSE",
        lookback_window=60,
        entry_zscore=Decimal("2.0"),
        exit_zscore=Decimal("0.0"),
        stoploss_zscore=Decimal("3.0"),
        max_half_life_days=5,
    )
    strategy = OuMeanReversionStrategy(config)
    assert strategy.name == "ou_mean_reversion"
    assert strategy.config.lookback_window == 60
    assert strategy.config.max_half_life_days == 5
