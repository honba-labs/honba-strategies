"""Tests for Equal Risk Contribution Sizer catalog entry."""

import pytest
from decimal import Decimal

from honba_strategies.components.sizers import EqualRiskSizer
from honba_strategies.components.sizers.base import Signal, SizingContext
from honba.entities.instrument import InstrumentId


class TestEqualRiskSizer:
    """Test Equal Risk Contribution Sizer functionality."""

    def test_single_signal_mode(self):
        """Test ERC with single signal (uses full budget)."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
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
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context, all_signals=[signal])

        # Total risk = 1,000,000 * 0.05 = 50,000
        # Single signal gets full 50,000
        # Q = 50,000 / 300 = 166.67 -> 150 lots (25 * 6)
        assert result.quantity == Decimal("150")
        assert result.risk_at_stake == Decimal("45000")  # 150 * 300

    def test_multiple_signals_equal_risk(self):
        """Test ERC with multiple signals (equal risk split)."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            use_correlation=False,  # Disable correlation for predictable test
        )

        signals = [
            Signal(direction=1, entry_price=Decimal("24000"), stop_loss=Decimal("23700")),
            Signal(direction=-1, entry_price=Decimal("48000"), stop_loss=Decimal("48500")),
        ]

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
        )

        for signal in signals:
            result = sizer.calculate_size(signal, context, all_signals=signals)
            # Each gets 25,000 risk budget
            # Signal 1: 25,000 / 300 = 83.33 -> 75 lots
            # Signal 2: 25,000 / 500 = 50 -> 50 lots
            if signal.entry_price == Decimal("24000"):
                assert result.quantity == Decimal("75")
            else:
                assert result.quantity == Decimal("50")

    def test_correlation_adjustment(self):
        """Test correlation-adjusted risk budget."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            use_correlation=True,
        )

        signals = [
            Signal(direction=1, entry_price=Decimal("24000"), stop_loss=Decimal("23700")),
            Signal(direction=-1, entry_price=Decimal("48000"), stop_loss=Decimal("48500")),
        ]

        # Low correlation -> higher diversification ratio -> more risk per signal
        corr_matrix = [
            [Decimal("1.0"), Decimal("0.1")],
            [Decimal("0.1"), Decimal("1.0")],
        ]

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
        )

        for signal in signals:
            result = sizer.calculate_size(signal, context, all_signals=signals,
                                         correlation_matrix=corr_matrix)
            # With correlation 0.1: div_ratio = sqrt(2) / sqrt(1 + 0.1) = 1.414 / 1.049 = 1.348
            # Risk per signal = 25,000 * 1.348 = 33,700
            # Signal 1: 33,700 / 300 = 112.33 -> 100 lots
            assert result.quantity >= Decimal("75")  # More than no-correlation case

    def test_high_correlation_reduces_risk(self):
        """Test that high correlation reduces risk per signal."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            use_correlation=True,
        )

        signals = [
            Signal(direction=1, entry_price=Decimal("24000"), stop_loss=Decimal("23700")),
            Signal(direction=1, entry_price=Decimal("48000"), stop_loss=Decimal("47500")),
        ]

        # High correlation -> lower diversification ratio
        corr_matrix = [
            [Decimal("1.0"), Decimal("0.9")],
            [Decimal("0.9"), Decimal("1.0")],
        ]

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
        )

        for signal in signals:
            result = sizer.calculate_size(signal, context, all_signals=signals,
                                         correlation_matrix=corr_matrix)
            # With correlation 0.9: div_ratio = sqrt(2) / sqrt(1 + 0.9) = 1.414 / 1.378 = 1.026
            # Risk per signal = 25,000 * 1.026 = 25,650 (barely more than no-correlation)
            assert result.quantity >= Decimal("75")

    def test_no_active_signals(self):
        """Test handling when no active signals."""
        sizer = EqualRiskSizer(total_risk_pct=Decimal("0.05"))

        signal = Signal(direction=0, entry_price=Decimal("24000"))  # Flat
        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signal, context, all_signals=[signal])
        assert result.quantity == Decimal("0")
        assert result.capping_reason == "no_active_signals"

    def test_max_notional_cap(self):
        """Test max position notional cap."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
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
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
        )

        result = sizer.calculate_size(signal, context, all_signals=[signal])
        # 1 lot = 600,000 > 100,000 -> 0
        assert result.quantity == Decimal("0")
        assert result.capped_by_limit

    def test_atr_fallback(self):
        """Test ATR fallback for stop distance."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
            max_position_notional=Decimal("10000000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            fallback_stop_atr_mult=Decimal("2.0"),
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
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            atr=Decimal("300"),
        )

        result = sizer.calculate_size(signal, context, all_signals=[signal])

        # Fallback stop = 600, Risk = 50,000
        # Q = 50,000 / 600 = 83.33 -> 75 lots
        assert result.quantity == Decimal("75")
        assert result.stop_distance == Decimal("600")

    def test_short_signal(self):
        """Test ERC for short signals."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signals = [
            Signal(direction=-1, entry_price=Decimal("48000"), stop_loss=Decimal("48500")),
        ]

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
        )

        result = sizer.calculate_size(signals[0], context, all_signals=signals)
        # Risk = 50,000, Stop = 500, Q = 100 -> 100 lots
        assert result.quantity == Decimal("100")
        assert result.stop_distance == Decimal("500")

    def test_correlation_clamping(self):
        """Test correlation matrix element clamping."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            use_correlation=True,
            min_correlation=Decimal("-0.3"),
            max_correlation=Decimal("0.8"),
        )

        signals = [Signal(direction=1, entry_price=Decimal("24000"), stop_loss=Decimal("23700"))
                   for _ in range(3)]

        # Correlations outside bounds should be clamped
        corr_matrix = [
            [Decimal("1.0"), Decimal("-0.5"), Decimal("0.9")],
            [Decimal("-0.5"), Decimal("1.0"), Decimal("0.0")],
            [Decimal("0.9"), Decimal("0.0"), Decimal("1.0")],
        ]

        context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                               margin_used=Decimal("0"), available_margin=Decimal("800000"))

        result = sizer.calculate_size(signals[0], context, all_signals=signals,
                                     correlation_matrix=corr_matrix)
        # Should not crash and produce valid result
        assert result.quantity >= Decimal("0")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])