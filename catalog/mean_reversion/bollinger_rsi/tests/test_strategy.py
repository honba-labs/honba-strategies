"""Tests for Bollinger Band + RSI strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.mean_reversion import BollingerRsiStrategy, BollingerRsiConfig


def test_bollinger_rsi_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = BollingerRsiConfig(
        name="bollinger_rsi",
        symbol="RELIANCE",
        exchange="NSE",
        bb_period=20,
        bb_std_dev=Decimal("2.0"),
        rsi_period=14,
        rsi_oversold=Decimal("25"),
        rsi_overbought=Decimal("75"),
    )
    strategy = BollingerRsiStrategy(config)
    assert strategy.name == "bollinger_rsi"
    assert strategy.config.bb_period == 20
    assert strategy.config.rsi_period == 14
    assert strategy.config.rsi_oversold == Decimal("25")