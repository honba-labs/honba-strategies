"""Tests for Kelly Criterion Sizer catalog entry."""

from decimal import Decimal

import pytest
from honba.entities.instrument import InstrumentId

from honba_strategies.components.sizers import KellySizer
from honba_strategies.components.sizers.base import Signal, SizingContext


class TestKellySizer:
    """Test Kelly Criterion Sizer functionality."""

    def test_basic_kelly_calculation(self):
        """Test basic Kelly fraction computation."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
            kelly_fraction=Decimal("0.5"),  # Half-Kelly
        )

        # Full Kelly = 0.55 - 0.45/1.5 = 0.55 - 0.3 = 0.25
        # Half Kelly = 0.125
        kelly_full = sizer._compute_kelly_fraction() / sizer.kelly_fraction
        assert abs(kelly_full - Decimal("0.25")) < Decimal("0.001")

    def test_kelly_with_explicit_stop(self):
        """Test Kelly sizing with explicit stop-loss."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
            kelly_fraction=Decimal("0.5"),
            max_position_notional=Decimal("500000"),
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

        # Full Kelly = 0.25, Half Kelly = 0.125
        # Risk amount = 1,000,000 * 0.125 = 125,000
        # Raw quantity = 125,000 / 300 = 416.67
        # Discretized to lot 25 = 400
        # But max notional 500,000 / 24,000 = 20.8 -> 0 lots
        # Actually 400 * 24000 = 9,600,000 > 500,000 cap
        assert result.quantity == Decimal("0")
        assert result.capped_by_limit
        assert "notional" in result.capping_reason.lower()

    def test_kelly_with_higher_notional_cap(self):
        """Test Kelly sizing with higher notional cap."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
            kelly_fraction=Decimal("0.5"),
            max_position_notional=Decimal("10000000"),
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

        # Half Kelly = 0.125, Risk = 125,000, Q = 416.67 -> 400 lots
        # 400 * 24000 = 9,600,000 < 10,000,000 cap
        assert result.quantity == Decimal("400")
        assert result.risk_at_stake == Decimal("120000")  # 400 * 300

    def test_signal_metadata_override(self):
        """Test that signal metadata can override win rate."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
            kelly_fraction=Decimal("0.5"),
            max_position_notional=Decimal("10000000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        # Signal with better win rate
        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("23700"),
            metadata={"win_rate": "0.65", "win_loss_ratio": "2.0"},
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

        # Full Kelly = 0.65 - 0.35/2 = 0.65 - 0.175 = 0.475
        # Half Kelly = 0.2375
        # Risk = 237,500, Q = 791.67 -> 775 lots
        assert result.quantity >= Decimal("750")

    def test_kelly_fraction_clamping(self):
        """Test Kelly fraction min/max clamping."""
        # High win rate that would give Kelly > max_kelly_fraction
        sizer = KellySizer(
            win_rate=Decimal("0.80"),
            win_loss_ratio=Decimal("3.0"),
            kelly_fraction=Decimal("1.0"),
            min_kelly_fraction=Decimal("0.0"),
            max_kelly_fraction=Decimal("0.5"),  # Cap at 50%
        )

        kelly = sizer._compute_kelly_fraction()
        # Full Kelly = 0.8 - 0.2/3 = 0.733, but capped at 0.5
        assert kelly == Decimal("0.5")

    def test_no_valid_stop_distance(self):
        """Test handling when no valid stop distance."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
        )

        signal = Signal(direction=1, entry_price=Decimal("24000"))
        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")
        assert "stop" in result.capping_reason.lower()

    def test_atr_fallback(self):
        """Test ATR fallback for stop distance."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
            kelly_fraction=Decimal("0.5"),
            fallback_stop_atr_mult=Decimal("2.0"),
            max_position_notional=Decimal("10000000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=None,
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
        # Half Kelly = 0.125, Risk = 125,000
        # Q = 125,000 / 600 = 208.33 -> 200 lots
        assert result.quantity == Decimal("200")
        assert result.stop_distance == Decimal("600")

    def test_short_signal(self):
        """Test Kelly sizing for short signals."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
            kelly_fraction=Decimal("0.5"),
            max_position_notional=Decimal("10000000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=-1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("24300"),
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
        assert result.quantity == Decimal("400")
        assert result.stop_distance == Decimal("300")

    def test_invalid_kelly_params(self):
        """Test handling of invalid Kelly parameters."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
        )

        # Signal with win_rate = 1.0 (invalid)
        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("23700"),
            metadata={"win_rate": "1.0"},
        )

        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")
        assert "kelly" in result.capping_reason.lower()

    def test_flat_signal(self):
        """Test flat signal returns zero."""
        sizer = KellySizer(win_rate=Decimal("0.55"), win_loss_ratio=Decimal("1.5"))

        signal = Signal(direction=0, entry_price=Decimal("24000"))
        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])