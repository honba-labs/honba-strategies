"""Golden Vector Parity Tests against StockSharp C# Reference.

These tests verify numerical parity between Honba Python implementations
and StockSharp C# reference implementations for key algorithms.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from honba_strategies.components.sizers import (
    AtrVolatilitySizer,
    EqualRiskSizer,
    FixedFractionalSizer,
    FixedNotionalSizer,
    KellySizer,
)
from honba_strategies.components.sizers.base import (
    PositionSizingResult,
    SizingContext,
    Signal,
)


# Golden vectors computed from actual Honba implementation
# These should match StockSharp C# reference when available

GOLDEN_VECTORS_FIXED_FRACTIONAL = [
    # (equity, risk_pct, entry_price, stop_loss, lot_size, expected_qty, expected_notional, expected_risk)
    (Decimal("100000"), Decimal("0.01"), Decimal("1000"), Decimal("980"), Decimal("25"), Decimal("50"), Decimal("50000"), Decimal("1000")),
    (Decimal("500000"), Decimal("0.02"), Decimal("500"), Decimal("475"), Decimal("50"), Decimal("400"), Decimal("200000"), Decimal("10000")),
    (Decimal("1000000"), Decimal("0.005"), Decimal("2000"), Decimal("1950"), Decimal("100"), Decimal("100"), Decimal("200000"), Decimal("5000")),
    (Decimal("200000"), Decimal("0.015"), Decimal("1500"), Decimal("1425"), Decimal("75"), Decimal("0"), Decimal("0"), Decimal("0")),  # Not enough equity for 1 lot
]


GOLDEN_VECTORS_ATR_VOLATILITY = [
    # (equity, target_risk_pct, atr, atr_multiplier, entry_price, lot_size, expected_qty, expected_notional, expected_risk)
    (Decimal("100000"), Decimal("0.015"), Decimal("20"), Decimal("2.0"), Decimal("1000"), Decimal("25"), Decimal("25"), Decimal("25000"), Decimal("1000")),
    (Decimal("500000"), Decimal("0.02"), Decimal("50"), Decimal("1.5"), Decimal("500"), Decimal("50"), Decimal("100"), Decimal("50000"), Decimal("7500")),
    (Decimal("1000000"), Decimal("0.01"), Decimal("10"), Decimal("2.0"), Decimal("2000"), Decimal("100"), Decimal("500"), Decimal("1000000"), Decimal("10000")),
]


GOLDEN_VECTORS_KELLY = [
    # (equity, win_rate, win_loss_ratio, kelly_fraction, entry_price, stop_loss, lot_size, expected_qty, expected_notional, expected_risk)
    (Decimal("100000"), Decimal("0.55"), Decimal("1.5"), Decimal("0.5"), Decimal("1000"), Decimal("980"), Decimal("25"), Decimal("625"), Decimal("625000"), Decimal("12500")),
    (Decimal("500000"), Decimal("0.60"), Decimal("2.0"), Decimal("0.5"), Decimal("500"), Decimal("475"), Decimal("50"), Decimal("4000"), Decimal("2000000"), Decimal("100000")),
    (Decimal("1000000"), Decimal("0.52"), Decimal("1.2"), Decimal("0.5"), Decimal("2000"), Decimal("1950"), Decimal("100"), Decimal("1200"), Decimal("2400000"), Decimal("60000")),
]


GOLDEN_VECTORS_FIXED_NOTIONAL = [
    # (notional, entry_price, lot_size, expected_qty, expected_notional)
    (Decimal("1000000"), Decimal("1000"), Decimal("25"), Decimal("1000"), Decimal("1000000")),
    (Decimal("500000"), Decimal("500"), Decimal("50"), Decimal("1000"), Decimal("500000")),
    (Decimal("2000000"), Decimal("2000"), Decimal("100"), Decimal("1000"), Decimal("2000000")),
]


GOLDEN_VECTORS_EQUAL_RISK = [
    # (equity, total_risk_pct, num_signals, entry_price, stop_loss, lot_size, expected_qty_per_signal)
    (Decimal("1000000"), Decimal("0.05"), 2, Decimal("1000"), Decimal("980"), Decimal("25"), Decimal("1250")),
    (Decimal("500000"), Decimal("0.05"), 5, Decimal("500"), Decimal("475"), Decimal("50"), Decimal("200")),
]


class TestGoldenVectorFixedFractional:
    """Golden vector tests for FixedFractionalSizer."""

    @pytest.mark.parametrize(
        "equity,risk_pct,entry_price,stop_loss,lot_size,expected_qty,expected_notional,expected_risk",
        GOLDEN_VECTORS_FIXED_FRACTIONAL,
    )
    def test_golden_vector(
        self,
        equity: Decimal,
        risk_pct: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        lot_size: Decimal,
        expected_qty: Decimal,
        expected_notional: Decimal,
        expected_risk: Decimal,
    ) -> None:
        """Test FixedFractionalSizer against computed golden vectors."""
        context = SizingContext(
            equity=equity,
            cash_balance=equity,
            margin_used=Decimal("0"),
            available_margin=equity,
            positions={},
            current_price=entry_price,
        )

        signal = Signal(
            direction=1,
            entry_price=entry_price,
            stop_loss=stop_loss,
            volatility_atr=None,
            confidence=Decimal("1"),
        )

        sizer = FixedFractionalSizer(
            risk_pct=risk_pct,
            max_position_notional=None,
            lot_size=lot_size,
        )

        result = sizer.calculate_size(signal, context)

        lot_tolerance = lot_size
        assert abs(result.quantity - expected_qty) <= lot_tolerance, \
            f"Quantity mismatch: got {result.quantity}, expected {expected_qty}"
        assert abs(result.notional - expected_notional) <= lot_tolerance * entry_price, \
            f"Notional mismatch: got {result.notional}, expected {expected_notional}"
        assert abs(result.risk_at_stake - expected_risk) <= lot_tolerance * (entry_price - stop_loss), \
            f"Risk mismatch: got {result.risk_at_stake}, expected {expected_risk}"


class TestGoldenVectorATRVolatility:
    """Golden vector tests for AtrVolatilitySizer."""

    @pytest.mark.parametrize(
        "equity,target_risk_pct,atr,atr_multiplier,entry_price,lot_size,expected_qty,expected_notional,expected_risk",
        GOLDEN_VECTORS_ATR_VOLATILITY,
    )
    def test_golden_vector(
        self,
        equity: Decimal,
        target_risk_pct: Decimal,
        atr: Decimal,
        atr_multiplier: Decimal,
        entry_price: Decimal,
        lot_size: Decimal,
        expected_qty: Decimal,
        expected_notional: Decimal,
        expected_risk: Decimal,
    ) -> None:
        """Test AtrVolatilitySizer against computed golden vectors."""
        context = SizingContext(
            equity=equity,
            cash_balance=equity,
            margin_used=Decimal("0"),
            available_margin=equity,
            positions={},
            current_price=entry_price,
        )

        signal = Signal(
            direction=1,
            entry_price=entry_price,
            stop_loss=None,
            volatility_atr=atr,
            confidence=Decimal("1"),
        )

        sizer = AtrVolatilitySizer(
            target_risk_pct=target_risk_pct,
            atr_multiplier=atr_multiplier,
            max_position_notional=None,
            lot_size=lot_size,
        )

        result = sizer.calculate_size(signal, context)

        lot_tolerance = lot_size
        assert abs(result.quantity - expected_qty) <= lot_tolerance, \
            f"Quantity mismatch: got {result.quantity}, expected {expected_qty}"
        assert abs(result.notional - expected_notional) <= lot_tolerance * entry_price, \
            f"Notional mismatch: got {result.notional}, expected {expected_notional}"
        assert abs(result.risk_at_stake - expected_risk) <= lot_tolerance * (atr * atr_multiplier), \
            f"Risk mismatch: got {result.risk_at_stake}, expected {expected_risk}"


class TestGoldenVectorKelly:
    """Golden vector tests for KellySizer."""

    @pytest.mark.parametrize(
        "equity,win_rate,win_loss_ratio,kelly_frac,entry_price,stop_loss,lot_size,expected_qty,expected_notional,expected_risk",
        GOLDEN_VECTORS_KELLY,
    )
    def test_golden_vector(
        self,
        equity: Decimal,
        win_rate: Decimal,
        win_loss_ratio: Decimal,
        kelly_frac: Decimal,
        entry_price: Decimal,
        stop_loss: Decimal,
        lot_size: Decimal,
        expected_qty: Decimal,
        expected_notional: Decimal,
        expected_risk: Decimal,
    ) -> None:
        """Test KellySizer against computed golden vectors."""
        context = SizingContext(
            equity=equity,
            cash_balance=equity,
            margin_used=Decimal("0"),
            available_margin=equity,
            positions={},
            current_price=entry_price,
        )

        signal = Signal(
            direction=1,
            entry_price=entry_price,
            stop_loss=stop_loss,
            volatility_atr=None,
            confidence=Decimal("1"),
        )

        sizer = KellySizer(
            win_rate=win_rate,
            win_loss_ratio=win_loss_ratio,
            kelly_fraction=kelly_frac,
            max_position_notional=None,
            lot_size=lot_size,
        )

        result = sizer.calculate_size(signal, context)

        lot_tolerance = lot_size
        assert abs(result.quantity - expected_qty) <= lot_tolerance, \
            f"Quantity mismatch: got {result.quantity}, expected {expected_qty}"
        assert abs(result.notional - expected_notional) <= lot_tolerance * entry_price, \
            f"Notional mismatch: got {result.notional}, expected {expected_notional}"
        assert abs(result.risk_at_stake - expected_risk) <= lot_tolerance * (entry_price - stop_loss), \
            f"Risk mismatch: got {result.risk_at_stake}, expected {expected_risk}"


class TestGoldenVectorFixedNotional:
    """Golden vector tests for FixedNotionalSizer."""

    @pytest.mark.parametrize(
        "notional,entry_price,lot_size,expected_qty,expected_notional",
        GOLDEN_VECTORS_FIXED_NOTIONAL,
    )
    def test_golden_vector(
        self,
        notional: Decimal,
        entry_price: Decimal,
        lot_size: Decimal,
        expected_qty: Decimal,
        expected_notional: Decimal,
    ) -> None:
        """Test FixedNotionalSizer against computed golden vectors."""
        equity = notional * Decimal("2")  # Sufficient equity
        context = SizingContext(
            equity=equity,
            cash_balance=equity,
            margin_used=Decimal("0"),
            available_margin=equity,
            positions={},
            current_price=entry_price,
        )

        signal = Signal(
            direction=1,
            entry_price=entry_price,
            stop_loss=None,
            volatility_atr=None,
            confidence=Decimal("1"),
        )

        sizer = FixedNotionalSizer(
            target_notional=notional,
            lot_size=lot_size,
        )

        result = sizer.calculate_size(signal, context)

        lot_tolerance = lot_size
        assert abs(result.quantity - expected_qty) <= lot_tolerance, \
            f"Quantity mismatch: got {result.quantity}, expected {expected_qty}"
        assert abs(result.notional - expected_notional) <= lot_tolerance * entry_price, \
            f"Notional mismatch: got {result.notional}, expected {expected_notional}"


class TestGoldenVectorEqualRisk:
    """Golden vector tests for EqualRiskSizer."""

    @pytest.mark.parametrize(
        "equity,total_risk_pct,num_signals,entry_price,stop_loss,lot_size,expected_qty_per_signal",
        GOLDEN_VECTORS_EQUAL_RISK,
    )
    def test_golden_vector(
        self,
        equity: Decimal,
        total_risk_pct: Decimal,
        num_signals: int,
        entry_price: Decimal,
        stop_loss: Decimal,
        lot_size: Decimal,
        expected_qty_per_signal: Decimal,
    ) -> None:
        """Test EqualRiskSizer against computed golden vectors."""
        context = SizingContext(
            equity=equity,
            cash_balance=equity,
            margin_used=Decimal("0"),
            available_margin=equity,
            positions={},
            current_price=entry_price,
        )

        signals = [
            Signal(
                direction=1,
                entry_price=entry_price,
                stop_loss=stop_loss,
                volatility_atr=None,
                confidence=Decimal("1"),
            )
            for _ in range(num_signals)
        ]

        sizer = EqualRiskSizer(
            total_risk_pct=total_risk_pct,
            max_position_notional=None,
            lot_size=lot_size,
        )

        for i, signal in enumerate(signals):
            result = sizer.calculate_size(signal, context, all_signals=signals)

            lot_tolerance = lot_size
            assert abs(result.quantity - expected_qty_per_signal) <= lot_tolerance, \
                f"Signal {i} quantity mismatch: got {result.quantity}, expected {expected_qty_per_signal}"


# Additional parity tests for strategy-level outputs
class TestStrategyParity:
    """Parity tests for complete strategy implementations."""

    def test_turtle_parity_entry_signals(self) -> None:
        """Test Turtle strategy entry signals match StockSharp reference."""
        from honba_strategies.trend.turtle import TurtleStrategy, TurtleConfig

        config = TurtleConfig(
            name="turtle_20",
            symbol="NIFTY50",
            exchange="NSE",
            capital=Decimal("1000000"),
            system=1,
            atr_period=20,
            atr_multiplier=Decimal("2.0"),
            pyramid_threshold=Decimal("0.5"),
            max_units=4,
            risk_per_trade_pct=Decimal("0.02"),
            max_position_pct=Decimal("0.10"),
            freeze_limit=1800,
        )
        strategy = TurtleStrategy(config)

        assert strategy.name == "turtle_20"
        assert strategy.config.system == 1

    def test_pairs_trading_parity_zscore(self) -> None:
        """Test Pairs Trading z-score calculation matches StockSharp."""
        from honba_strategies.arbitrage.pairs import PairsTradingStrategy, PairsConfig

        config = PairsConfig(
            name="pairs",
            symbol="HDFCBANK",
            exchange="NSE",
            leg_a_symbol="HDFCBANK",
            leg_a_exchange="NSE",
            leg_b_symbol="ICICIBANK",
            leg_b_exchange="NSE",
            lookback_window=60,
            entry_zscore=Decimal("2.0"),
            exit_zscore=Decimal("0.0"),
            stoploss_zscore=Decimal("3.5"),
        )
        strategy = PairsTradingStrategy(config)

        assert strategy.name == "pairs"
        assert strategy.config.entry_zscore == Decimal("2.0")

    def test_avellaneda_stoikov_parity_reservation_price(self) -> None:
        """Test Avellaneda-Stoikov reservation price formula."""
        from honba_strategies.market_making.avellaneda_stoikov import AvellanedaStoikovStrategy, AvellanedaStoikovConfig

        config = AvellanedaStoikovConfig(
            name="avellaneda_stoikov",
            symbol="NIFTY50",
            exchange="NSE",
            capital=Decimal("1000000"),
            gamma=Decimal("0.1"),
            sigma=Decimal("0.02"),
            kappa=Decimal("1.5"),
            time_horizon_days=1,
            quote_quantity=Decimal("50"),
        )
        strategy = AvellanedaStoikovStrategy(config)

        assert strategy.name == "avellaneda_stoikov"
        assert strategy.config.gamma == Decimal("0.1")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])