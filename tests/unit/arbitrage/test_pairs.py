"""Unit tests for Pairs Trading strategy."""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from honba.domain import Bar, InstrumentId

from honba_strategies.arbitrage import PairsTradingStrategy, PairsConfig


def make_bar(symbol, close, ts=None):
    """Create a bar for testing."""
    iid = InstrumentId(symbol, "NSE")
    return Bar(iid, ts or 1, close, close, close, close, 1000.0)


class TestPairsTradingStrategy:
    """Test Pairs Trading strategy."""

    def build(self, **params):
        """Build Pairs Trading strategy with config overrides."""
        config = PairsConfig(
            name="pairs_trading",
            symbol="HDFCBANK",
            leg_a_symbol="HDFCBANK",
            leg_b_symbol="ICICIBANK",
            entry_zscore=Decimal("2.0"),
            exit_zscore=Decimal("0.0"),
            stoploss_zscore=Decimal("3.5"),
            **params,
        )
        return PairsTradingStrategy(config), config

    def test_pairs_strategy_initialization(self):
        """Test that pairs strategy initializes correctly."""
        s, cfg = self.build()
        assert s.name == "pairs"
        assert s.leg_a_symbol == "HDFCBANK"
        assert s.leg_b_symbol == "ICICIBANK"
        assert s.entry_zscore == 2.0
        assert s.exit_zscore == 0.0
        assert s.stoploss_zscore == 3.5

    def test_pairs_config_validation(self):
        """Test that config validation works."""
        with pytest.raises(ValueError):
            PairsConfig(
                name="test",
                symbol="TEST",
                entry_zscore=Decimal("1.0"),
                exit_zscore=Decimal("2.0"),
            )

        with pytest.raises(ValueError):
            PairsConfig(
                name="test",
                symbol="TEST",
                entry_zscore=Decimal("2.0"),
                stoploss_zscore=Decimal("1.5"),
            )

    @patch('numpy.polyfit')
    def test_cointegration_estimation(self, mock_polyfit):
        """Test cointegration estimation."""
        mock_polyfit.return_value = (0.95, 0.02)  # beta, alpha

        s, cfg = self.build()
        s.on_start()

        # Feed enough bars to trigger cointegration estimation
        for i in range(35):
            s.on_bar(make_bar("HDFCBANK", 1600 + i * 0.5, i + 1))
            s.on_bar(make_bar("ICICIBANK", 950 + i * 0.3, i + 1))

        assert s._cointegration_validated or s._hedge_ratio_estimated > 0