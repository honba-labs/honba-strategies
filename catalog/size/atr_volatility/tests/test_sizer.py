"""Tests for ATR Volatility Sizer catalog entry."""

import pytest
from decimal import Decimal

from honba_strategies.components.sizers import AtrVolatilitySizer
from honba_strategies.components.sizers.base import Signal, SizingContext
from honba.entities.instrument import InstrumentId


class TestAtrVolatilitySizer:
    """Test ATR Volatility Sizer functionality."""

    def test_inverse_vol_mode_basic(self):
        """Test basic inverse volatility sizing."""
        sizer = AtrVolatilitySizer(
            target_risk_pct=Decimal("0.015"),
            atr_multiplier=Decimal("2.0"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
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

        # Stop distance = 300 * 2 = 600
        # Risk amount = 1,000,000 * 0.015 = 15,000
        # Raw quantity = 15,000 / 600 = 25
        # Discretized to lot 25 = 25
        assert result.quantity == Decimal("25")
        assert result.stop_distance == Decimal("600")
        assert result.risk_at_stake == Decimal("15000")

    def test_volatility_targeting_mode(self):
        """Test portfolio volatility targeting mode."""
        sizer = AtrVolatilitySizer(
            target_annual_vol=Decimal("0.15"),  # 15% annual vol
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            trading_days=252,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
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

        # Daily vol target = 0.15 / sqrt(252) ≈ 0.00945
        # Q = 0.00945 * 1,000,000 / (24000 * 300) ≈ 1.31 -> 0 lots (25 min)
        # Actually with price=24000, atr=300: Q = 0.00945 * 1e6 / (24000 * 300) = 0.00131
        # So quantity should be 0 (less than 1 lot of 25)
        assert result.quantity == Decimal("0")

    def test_volatility_targeting_with_higher_equity(self):
        """Test volatility targeting with higher equity."""
        sizer = AtrVolatilitySizer(
            target_annual_vol=Decimal("0.15"),
            max_position_notional=Decimal("5000000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            trading_days=252,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            volatility_atr=Decimal("300"),
        )

        context = SizingContext(
            equity=Decimal("10000000"),  # 1 crore
            cash_balance=Decimal("8000000"),
            margin_used=Decimal("2000000"),
            available_margin=Decimal("6000000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
            atr=Decimal("300"),
        )

        result = sizer.calculate_size(signal, context)

        # Daily vol target = 0.15 / sqrt(252) ≈ 0.00945
        # Q = 0.00945 * 10,000,000 / (24000 * 300) ≈ 13.1 -> 0 lots (25 min)
        # Still less than 1 lot
        assert result.quantity == Decimal("0")

    def test_volatility_targeting_with_small_atr(self):
        """Test volatility targeting with small ATR (larger positions)."""
        sizer = AtrVolatilitySizer(
            target_annual_vol=Decimal("0.15"),
            max_position_notional=Decimal("5000000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            trading_days=252,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            volatility_atr=Decimal("50"),  # Low ATR
        )

        context = SizingContext(
            equity=Decimal("10000000"),
            cash_balance=Decimal("8000000"),
            margin_used=Decimal("2000000"),
            available_margin=Decimal("6000000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
            atr=Decimal("50"),
        )

        result = sizer.calculate_size(signal, context)

        # Daily vol target = 0.15 / sqrt(252) ≈ 0.00945
        # Q = 0.00945 * 10,000,000 / (24000 * 50) ≈ 78.75 -> 75 lots (25 * 3)
        assert result.quantity == Decimal("75")
        assert result.notional == Decimal("1800000")  # 75 * 24000

    def test_no_atr_available(self):
        """Test handling when ATR is not available."""
        sizer = AtrVolatilitySizer(target_risk_pct=Decimal("0.015"))

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            volatility_atr=None,
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
        )

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")
        assert result.capping_reason == "no_atr_available"

    def test_max_notional_cap(self):
        """Test max position notional cap."""
        sizer = AtrVolatilitySizer(
            target_risk_pct=Decimal("0.015"),
            atr_multiplier=Decimal("2.0"),
            max_position_notional=Decimal("100000"),  # Low cap
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
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

        # 1 lot = 600,000 > 100,000 cap -> 0
        assert result.quantity == Decimal("0")
        assert result.capped_by_limit

    def test_short_signal(self):
        """Test sizing for short signals."""
        sizer = AtrVolatilitySizer(
            target_risk_pct=Decimal("0.015"),
            atr_multiplier=Decimal("2.0"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=-1,
            entry_price=Decimal("24000"),
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
        assert result.quantity == Decimal("25")
        assert result.stop_distance == Decimal("600")

    def test_flat_signal(self):
        """Test flat signal returns zero."""
        sizer = AtrVolatilitySizer(target_risk_pct=Decimal("0.015"))

        signal = Signal(direction=0, entry_price=Decimal("24000"), volatility_atr=Decimal("300"))
        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])