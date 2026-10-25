"""Unit tests for Basket Arbitrage strategy."""

from decimal import Decimal

import pytest
from honba.domain import Bar, InstrumentId

from honba_strategies.arbitrage import BasketArbitrageStrategy, BasketConfig


def make_bar(symbol, close, ts=None):
    """Create a bar for testing."""
    iid = InstrumentId(symbol, "NSE")
    return Bar(iid, ts or 1, close, close, close, close, 1000.0)


class TestBasketArbitrageStrategy:
    """Test Basket Arbitrage strategy."""

    def build(self, **params):
        """Build Basket Arbitrage strategy with config overrides."""
        config = BasketConfig(
            name="basket_arbitrage",
            symbol="NIFTYBEES",
            exchange="NSE",
            etf_symbol="NIFTYBEES",
            etf_exchange="NSE",
            constituents=["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "HINDUNILVR", "ITC", "SBIN", "BHARTIARTL", "KOTAKBANK"],
            min_basis_bps=Decimal("10"),
            rebalance_threshold_bps=Decimal("5"),
            **params,
        )
        return BasketArbitrageStrategy(config), config

    def test_basket_arbitrage_initialization(self):
        """Test that basket arbitrage strategy initializes correctly."""
        s, _cfg = self.build()
        assert s.name == "basket"
        assert s.config.etf_symbol == "NIFTYBEES"
        assert len(s.config.constituents) >= 10  # Minimum for basket arbitrage

    def test_basket_config_validation(self):
        """Test that config validation requires enough constituents."""
        with pytest.raises(ValueError):
            BasketConfig(
                name="test",
                symbol="TEST",
                constituents=["RELIANCE", "TCS"],
            )

    def test_synthetic_basket_calculation(self):
        """Test synthetic basket price calculation."""
        s, _cfg = self.build()
        s.on_start()

        # Set some constituent prices
        s._constituent_prices = {"RELIANCE": 2500, "TCS": 3500, "INFY": 1500}

        # Should calculate weighted average
        synthetic = s._calculate_synthetic_basket_price()
        assert synthetic > 0
