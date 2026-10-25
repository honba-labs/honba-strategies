"""Tests for Fixed Fractional Sizer catalog entry."""

import pytest
from decimal import Decimal

from honba_strategies.components.sizers import FixedFractionalSizer
from honba_strategies.components.sizers.base import Signal, SizingContext
from honba.entities.instrument import InstrumentId


class TestFixedFractionalSizer:
    """Test Fixed Fractional Sizer functionality."""

    def test_basic_sizing_with_explicit_stop(self):
        """Test sizing with explicit stop-loss in signal."""
        sizer = FixedFractionalSizer(
            risk_pct=Decimal("0.01"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("23700"),  # 300 points stop
            volatility_atr=Decimal("300"),
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("200000"),
            available_margin=Decimal("600000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
            atr=Decimal("300"),
        )

        result = sizer.calculate_size(signal, context)

        # Risk amount = 1,000,000 * 0.01 = 10,000
        # Stop distance = 24000 - 23700 = 300
        # Raw quantity = 10,000 / 300 = 33.33
        # Discretized to lot size 25 = 25
        assert result.quantity == Decimal("25")
        assert result.notional == Decimal("600000")  # 25 * 24000
        assert result.risk_at_stake == Decimal("7500")  # 25 * 300
        assert not result.capped_by_limit

    def test_sizing_hits_freeze_limit(self):
        """Test that freeze limit caps position size."""
        sizer = FixedFractionalSizer(
            risk_pct=Decimal("0.05"),  # 5% risk
            max_position_notional=Decimal("5000000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("23700"),
        )

        context = SizingContext(
            equity=Decimal("10000000"),  # 1 crore equity
            cash_balance=Decimal("8000000"),
            margin_used=Decimal("2000000"),
            available_margin=Decimal("6000000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)

        # Risk amount = 10,000,000 * 0.05 = 500,000
        # Raw quantity = 500,000 / 300 = 1666.67
        # But freeze limit is 1800, lot size 25 -> 1800 contracts max
        # 1800 / 25 = 72 lots = 1800 contracts
        assert result.quantity <= Decimal("1800")
        assert result.capped_by_limit
        assert "freeze" in result.capping_reason.lower()

    def test_sizing_hits_max_notional(self):
        """Test that max position notional caps position size."""
        sizer = FixedFractionalSizer(
            risk_pct=Decimal("0.01"),
            max_position_notional=Decimal("100000"),  # Low cap
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("23700"),
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("200000"),
            available_margin=Decimal("600000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)

        # Max notional 100,000 / 24,000 = 4.16 -> discretized to lot 25 = 0
        # Actually with 25 lot size, 1 lot = 600,000 > 100,000 cap
        # So quantity should be 0
        assert result.quantity == Decimal("0")
        assert result.capped_by_limit

    def test_sizing_with_atr_fallback(self):
        """Test sizing uses ATR fallback when signal lacks explicit stop."""
        sizer = FixedFractionalSizer(
            risk_pct=Decimal("0.01"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            fallback_stop_atr_mult=Decimal("2.0"),
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=None,  # No explicit stop
            volatility_atr=Decimal("300"),
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("200000"),
            available_margin=Decimal("600000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
            atr=Decimal("300"),
        )

        result = sizer.calculate_size(signal, context)

        # Fallback stop = 2 * 300 = 600
        # Risk amount = 10,000
        # Raw quantity = 10,000 / 600 = 16.67 -> 0 lots (25 min)
        assert result.quantity == Decimal("0")  # Less than 1 lot

    def test_short_signal_sizing(self):
        """Test sizing for short signals."""
        sizer = FixedFractionalSizer(
            risk_pct=Decimal("0.01"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=-1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("24300"),  # Stop above entry for short
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("200000"),
            available_margin=Decimal("600000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)

        assert result.quantity == Decimal("25")
        assert result.risk_at_stake == Decimal("7500")  # 25 * 300

    def test_flat_signal_returns_zero(self):
        """Test that flat signals return zero size."""
        sizer = FixedFractionalSizer(risk_pct=Decimal("0.01"))

        signal = Signal(direction=0, entry_price=Decimal("24000"))
        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")
        assert result.capping_reason == "no_valid_stop_distance"

    def test_invalid_stop_distance(self):
        """Test handling of invalid stop distance (stop >= entry for long)."""
        sizer = FixedFractionalSizer(risk_pct=Decimal("0.01"))

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("24100"),  # Stop above entry - invalid for long
        )

        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")
        assert "invalid_stop" in result.capping_reason.lower()

    def test_max_risk_per_trade_cap(self):
        """Test max risk per trade cap."""
        sizer = FixedFractionalSizer(
            risk_pct=Decimal("0.01"),
            max_position_notional=Decimal("500000"),
            max_risk_per_trade=Decimal("5000"),  # Low cap
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("23700"),  # 300 stop
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("200000"),
            available_margin=Decimal("600000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)

        # Max risk 5000 / 300 = 16.67 -> 0 lots
        assert result.quantity == Decimal("0")
        assert result.capped_by_limit
        assert "risk" in result.capping_reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])