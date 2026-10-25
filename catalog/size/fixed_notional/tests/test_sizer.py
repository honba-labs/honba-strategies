"""Tests for Fixed Notional Sizer catalog entry."""

from decimal import Decimal

import pytest
from honba.entities.instrument import InstrumentId

from honba_strategies.components.sizers import FixedNotionalSizer
from honba_strategies.components.sizers.base import Signal, SizingContext


class TestFixedNotionalSizer:
    """Test Fixed Notional Sizer functionality."""

    def test_basic_notional_sizing(self):
        """Test basic fixed notional sizing."""
        sizer = FixedNotionalSizer(
            target_notional=Decimal("600000"),
            max_position_notional=Decimal("600000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)

        # Q = 600,000 / 24,000 = 25 -> 25 lots
        assert result.quantity == Decimal("25")
        assert result.notional == Decimal("600000")
        assert result.risk_at_stake == Decimal("0")  # No stop provided

    def test_notional_with_stop_loss(self):
        """Test notional sizing calculates risk when stop provided."""
        sizer = FixedNotionalSizer(
            target_notional=Decimal("600000"),
            max_position_notional=Decimal("600000"),
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
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)

        assert result.quantity == Decimal("25")
        assert result.notional == Decimal("600000")
        assert result.risk_at_stake == Decimal("7500")  # 25 * 300

    def test_max_notional_cap(self):
        """Test max position notional cap."""
        sizer = FixedNotionalSizer(
            target_notional=Decimal("1000000"),
            max_position_notional=Decimal("500000"),  # Lower cap
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(direction=1, entry_price=Decimal("24000"))
        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)

        # Target 1,000,000 / 24,000 = 41.67 -> 25 lots (600,000)
        # But max cap 500,000 / 24,000 = 20.83 -> 0 lots
        assert result.quantity == Decimal("0")
        assert result.capped_by_limit
        assert "notional" in result.capping_reason.lower()

    def test_freeze_limit(self):
        """Test exchange freeze limit."""
        sizer = FixedNotionalSizer(
            target_notional=Decimal("50000000"),  # 5 crore
            max_position_notional=Decimal("50000000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(direction=1, entry_price=Decimal("24000"))
        context = SizingContext(
            equity=Decimal("100000000"),
            cash_balance=Decimal("80000000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("80000000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)

        # 5 crore / 24,000 = 2083 -> capped at freeze 1800
        # 1800 / 25 = 72 lots = 1800 contracts
        assert result.quantity == Decimal("1800")
        assert result.capped_by_limit
        assert "freeze" in result.capping_reason.lower()

    def test_low_priced_instrument(self):
        """Test sizing for low-priced instruments."""
        sizer = FixedNotionalSizer(
            target_notional=Decimal("100000"),
            max_position_notional=Decimal("100000"),
            lot_size=Decimal("1"),  # Equity lot size = 1
            freeze_limit=1800,
        )

        signal = Signal(direction=1, entry_price=Decimal("250"))  # ₹250 stock
        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            instrument_id=InstrumentId("RELIANCE", "NSE"),
            current_price=Decimal("250"),
        )

        result = sizer.calculate_size(signal, context)

        # Q = 100,000 / 250 = 400 shares
        assert result.quantity == Decimal("400")
        assert result.notional == Decimal("100000")

    def test_short_signal(self):
        """Test fixed notional for short signals."""
        sizer = FixedNotionalSizer(
            target_notional=Decimal("600000"),
            max_position_notional=Decimal("600000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(direction=-1, entry_price=Decimal("24000"))
        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("25")
        assert result.notional == Decimal("600000")

    def test_flat_signal(self):
        """Test flat signal returns zero."""
        sizer = FixedNotionalSizer(target_notional=Decimal("100000"))

        signal = Signal(direction=0, entry_price=Decimal("24000"))
        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")
        assert result.capping_reason == "flat_signal"

    def test_invalid_price(self):
        """Test handling of invalid/zero price."""
        sizer = FixedNotionalSizer(target_notional=Decimal("100000"))

        signal = Signal(direction=1, entry_price=Decimal("0"))
        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")
        assert "price" in result.capping_reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])