"""Tests for Pairs Trading strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.arbitrage import PairsConfig, PairsTradingStrategy


def test_pairs_trading_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = PairsConfig(
        name="pairs",
        symbol="HDFCBANK",
        leg_a_symbol="HDFCBANK",
        leg_b_symbol="ICICIBANK",
        entry_zscore=Decimal("2.0"),
        exit_zscore=Decimal("0.0"),
        stoploss_zscore=Decimal("3.5"),
    )
    strategy = PairsTradingStrategy(config)
    assert strategy.name == "pairs"
    assert strategy.config.leg_a_symbol == "HDFCBANK"
    assert strategy.config.leg_b_symbol == "ICICIBANK"