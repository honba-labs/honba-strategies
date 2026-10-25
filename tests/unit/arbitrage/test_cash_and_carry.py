"""Unit tests for Cash-and-Carry strategy."""

from decimal import Decimal

import pytest
from honba.domain import Bar, InstrumentId

from honba_strategies.arbitrage import CashAndCarryConfig, CashAndCarryStrategy


def make_bar(symbol, close, ts=None):
    """Create a bar for testing."""
    iid = InstrumentId(symbol, "NSE")
    return Bar(iid, ts or 1, close, close, close, close, 1000.0)


class TestCashAndCarryStrategy:
    """Test Cash-and-Carry strategy."""

    def build(self, **params):
        """Build Cash-and-Carry strategy with config overrides."""
        config = CashAndCarryConfig(
            name="cash_and_carry",
            symbol="RELIANCE",
            spot_symbol="RELIANCE",
            futures_symbol="RELIANCE",
            futures_expiry="2026-12-25",
            min_basis_bps=Decimal("50"),
            lot_size=250,
            **params,
        )
        return CashAndCarryStrategy(config), config

    def test_cash_and_carry_initialization(self):
        """Test that cash-and-carry strategy initializes correctly."""
        s, _cfg = self.build()
        assert s.name == "cash_and_carry"
        assert s.config.spot_symbol == "RELIANCE"
        assert s.config.futures_expiry == "2026-12-25"
        assert s.config.min_basis_bps == Decimal("50")

    def test_cash_and_carry_config_validation(self):
        """Test that config validation requires futures_expiry."""
        with pytest.raises(ValueError):
            CashAndCarryConfig(
                name="test",
                symbol="TEST",
                futures_expiry="",
            )

    def test_cash_and_carry_fair_basis(self):
        """Test fair basis calculation."""
        s, _cfg = self.build()
        s.on_start()

        # Test with 30 days to expiry (directly call without patching)
        fair_basis = s._calculate_fair_basis(2500.0, 30)
        assert fair_basis > 0
