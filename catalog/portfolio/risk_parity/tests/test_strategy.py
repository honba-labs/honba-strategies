"""Tests for Risk Parity strategy (catalog entry)."""

from decimal import Decimal

from honba_strategies.portfolio import RiskParityStrategy, RiskParityConfig


def test_risk_parity_catalog_entry():
    config = RiskParityConfig(
        name="risk_parity",
        symbol="",
        exchange="NSE",
        lookback_window=60,
    )
    strategy = RiskParityStrategy(config)
    assert strategy.name == "risk_parity"
    assert strategy.config.lookback_window == 60
