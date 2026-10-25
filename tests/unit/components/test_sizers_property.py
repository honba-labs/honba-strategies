"""Property-based tests for position sizing engines using Hypothesis."""

from __future__ import annotations

from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from honba_strategies.components.sizers import (
    AtrVolatilitySizer,
    EqualRiskSizer,
    FixedFractionalSizer,
    FixedNotionalSizer,
    KellySizer,
)
from honba_strategies.components.sizers.base import (
    PositionSizingResult,
    Signal,
    SizingContext,
)


def sizing_context_strategy() -> st.SearchStrategy[SizingContext]:
    """Generate valid SizingContext objects."""
    return st.builds(
        SizingContext,
        equity=st.decimals(min_value="1000", max_value="10000000", places=2),
        cash_balance=st.decimals(min_value="1000", max_value="10000000", places=2),
        margin_used=st.decimals(min_value="0", max_value="5000000", places=2),
        available_margin=st.decimals(min_value="1000", max_value="10000000", places=2),
        positions=st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.decimals(min_value="-10000", max_value="10000", places=2),
        ),
    )


def signal_strategy() -> st.SearchStrategy[Signal]:
    """Generate valid Signal objects."""
    return st.builds(
        Signal,
        direction=st.sampled_from([1, -1]),
        entry_price=st.decimals(min_value="1", max_value="50000", places=2),
        stop_loss=st.one_of(
            st.none(),
            st.decimals(min_value="1", max_value="50000", places=2),
        ),
        volatility_atr=st.one_of(
            st.none(),
            st.decimals(min_value="0.01", max_value="5000", places=2),
        ),
        confidence=st.decimals(min_value="0", max_value="1", places=2),
    )


@given(context=sizing_context_strategy(), signal=signal_strategy())
@settings(max_examples=200, deadline=None)
def test_fixed_fractional_sizer_invariants(context: SizingContext, signal: Signal) -> None:
    """Test FixedFractionalSizer invariants."""
    lot_size = Decimal("25")
    sizer = FixedFractionalSizer(
        risk_pct=Decimal("0.01"),
        max_position_notional=Decimal("500000"),
        lot_size=lot_size,
    )

    result = sizer.calculate_size(signal, context)

    assert isinstance(result, PositionSizingResult)
    assert result.quantity >= 0
    assert result.notional <= Decimal("500000")

    if signal.stop_loss is None and signal.volatility_atr is None:
        assert result.quantity == 0
        assert result.capping_reason in ("no_valid_stop_distance", "invalid_stop_distance")


@given(context=sizing_context_strategy(), signal=signal_strategy())
@settings(max_examples=200, deadline=None)
def test_atr_volatility_sizer_invariants(context: SizingContext, signal: Signal) -> None:
    """Test AtrVolatilitySizer invariants."""
    lot_size = Decimal("1")
    sizer = AtrVolatilitySizer(
        target_risk_pct=Decimal("0.015"),
        atr_multiplier=Decimal("2.0"),
        max_position_notional=Decimal("1000000"),
        lot_size=lot_size,
    )

    result = sizer.calculate_size(signal, context)

    assert isinstance(result, PositionSizingResult)
    assert result.quantity >= 0
    assert result.quantity % lot_size == 0
    assert result.notional <= Decimal("1000000")


@given(context=sizing_context_strategy(), signal=signal_strategy())
@settings(max_examples=200, deadline=None)
def test_kelly_sizer_invariants(context: SizingContext, signal: Signal) -> None:
    """Test KellySizer invariants."""
    lot_size = Decimal("1")
    sizer = KellySizer(
        win_rate=Decimal("0.55"),
        win_loss_ratio=Decimal("1.5"),
        kelly_fraction=Decimal("0.5"),
        max_position_notional=Decimal("500000"),
        lot_size=lot_size,
    )

    result = sizer.calculate_size(signal, context)

    assert isinstance(result, PositionSizingResult)
    assert result.quantity >= 0
    assert result.quantity % lot_size == 0
    assert result.notional <= Decimal("500000")


@given(context=sizing_context_strategy(), signal=signal_strategy())
@settings(max_examples=200, deadline=None)
def test_fixed_notional_sizer_invariants(context: SizingContext, signal: Signal) -> None:
    """Test FixedNotionalSizer invariants."""
    target_notional = Decimal("100000")
    lot_size = Decimal("25")
    sizer = FixedNotionalSizer(
        target_notional=target_notional,
        lot_size=lot_size,
    )

    result = sizer.calculate_size(signal, context)

    assert isinstance(result, PositionSizingResult)
    assert result.quantity >= 0
    assert result.quantity % lot_size == 0
    lot_value = lot_size * signal.entry_price
    assert abs(result.notional - target_notional) <= lot_value


@given(
    context=sizing_context_strategy(),
    signals=st.lists(signal_strategy(), min_size=1, max_size=5),
)
@settings(max_examples=100, deadline=None)
def test_equal_risk_sizer_invariants(
    context: SizingContext, signals: list[Signal]
) -> None:
    """Test EqualRiskSizer invariants."""
    lot_size = Decimal("1")
    sizer = EqualRiskSizer(
        total_risk_pct=Decimal("0.05"),
        max_position_notional=Decimal("1000000"),
        lot_size=lot_size,
    )

    result = sizer.calculate_size(signals[0], context, all_signals=signals)

    assert isinstance(result, PositionSizingResult)
    assert result.quantity >= 0
    assert result.quantity % lot_size == 0
    assert result.notional <= Decimal("1000000")


@given(
    equity=st.decimals(min_value="1000", max_value="10000000", places=2),
    entry_price=st.decimals(min_value="1", max_value="50000", places=2),
    stop_distance=st.decimals(min_value="0.01", max_value="1000", places=2),
    lot_size=st.sampled_from([1, 25, 50, 75, 100]),
    risk_pct=st.decimals(min_value="0.001", max_value="0.1", places=4),
)
@settings(max_examples=500, deadline=None)
def test_fixed_fractional_mathematical_correctness(
    equity: Decimal,
    entry_price: Decimal,
    stop_distance: Decimal,
    lot_size: int,
    risk_pct: Decimal,
) -> None:
    """Test FixedFractionalSizer mathematical formula correctness."""
    from honba_strategies.components.sizers.fixed_fractional import FixedFractionalSizer

    context = SizingContext(
        equity=equity,
        cash_balance=equity,
        margin_used=Decimal("0"),
        available_margin=equity,
        positions={},
    )

    stop_loss = entry_price - stop_distance if stop_distance < entry_price else entry_price * Decimal("0.98")
    signal = Signal(
        direction=1,
        entry_price=entry_price,
        stop_loss=stop_loss,
        volatility_atr=None,
        confidence=Decimal("1"),
    )

    sizer = FixedFractionalSizer(
        risk_pct=risk_pct,
        max_position_notional=None,  # No cap
        lot_size=Decimal(str(lot_size)),
    )

    result = sizer.calculate_size(signal, context)

    risk_amount = equity * risk_pct
    actual_stop_distance = entry_price - stop_loss
    if actual_stop_distance > 0:
        raw_qty = risk_amount / actual_stop_distance
        expected_lots = int(raw_qty // lot_size)
        expected_qty = Decimal(str(expected_lots * lot_size))
    else:
        expected_qty = Decimal("0")

    assert abs(result.quantity - expected_qty) <= Decimal(str(lot_size))


@given(
    equity=st.decimals(min_value="1000", max_value="10000000", places=2),
    atr=st.decimals(min_value="0.1", max_value="5000", places=2),
    entry_price=st.decimals(min_value="1", max_value="50000", places=2),
    lot_size=st.sampled_from([1, 25, 50, 75, 100]),
    target_risk=st.decimals(min_value="0.005", max_value="0.05", places=4),
    atr_mult=st.decimals(min_value="1.0", max_value="3.0", places=2),
)
@settings(max_examples=500, deadline=None)
def test_atr_volatility_mathematical_correctness(
    equity: Decimal,
    atr: Decimal,
    entry_price: Decimal,
    lot_size: int,
    target_risk: Decimal,
    atr_mult: Decimal,
) -> None:
    """Test AtrVolatilitySizer mathematical formula correctness."""
    from honba_strategies.components.sizers.volatility import AtrVolatilitySizer

    context = SizingContext(
        equity=equity,
        cash_balance=equity,
        margin_used=Decimal("0"),
        available_margin=equity,
        positions={},
    )

    signal = Signal(
        direction=1,
        entry_price=entry_price,
        stop_loss=None,
        volatility_atr=atr,
        confidence=Decimal("1"),
    )

    sizer = AtrVolatilitySizer(
        target_risk_pct=target_risk,
        atr_multiplier=atr_mult,
        max_position_notional=None,
        lot_size=Decimal(str(lot_size)),
    )

    result = sizer.calculate_size(signal, context)

    denom = atr * atr_mult
    if denom > 0:
        raw_qty = (equity * target_risk) / denom
        expected_lots = int(raw_qty // lot_size)
        expected_qty = Decimal(str(expected_lots * lot_size))
    else:
        expected_qty = Decimal("0")

    assert abs(result.quantity - expected_qty) <= Decimal(str(lot_size))


@given(
    equity=st.decimals(min_value="1000", max_value="10000000", places=2),
    notional=st.decimals(min_value="1000", max_value="1000000", places=2),
    entry_price=st.decimals(min_value="1", max_value="50000", places=2),
    lot_size=st.sampled_from([1, 25, 50, 75, 100]),
)
@settings(max_examples=500, deadline=None)
def test_fixed_notional_mathematical_correctness(
    equity: Decimal,
    notional: Decimal,
    entry_price: Decimal,
    lot_size: int,
) -> None:
    """Test FixedNotionalSizer mathematical formula correctness."""
    from honba_strategies.components.sizers.fixed_notional import FixedNotionalSizer

    context = SizingContext(
        equity=equity,
        cash_balance=equity,
        margin_used=Decimal("0"),
        available_margin=equity,
        positions={},
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
        lot_size=Decimal(str(lot_size)),
    )

    result = sizer.calculate_size(signal, context)

    raw_lots = notional / (entry_price * Decimal(str(lot_size)))
    expected_lots = int(raw_lots)
    expected_qty = Decimal(str(expected_lots * lot_size))

    assert abs(result.quantity - expected_qty) <= Decimal(str(lot_size))
    assert result.notional <= notional + Decimal(str(lot_size)) * entry_price


@given(
    win_rate=st.decimals(min_value="0.51", max_value="0.9", places=2),
    win_loss_ratio=st.decimals(min_value="1.01", max_value="5.0", places=2),
    kelly_frac=st.decimals(min_value="0.1", max_value="1.0", places=2),
    equity=st.decimals(min_value="1000", max_value="10000000", places=2),
    entry_price=st.decimals(min_value="1", max_value="50000", places=2),
    lot_size=st.sampled_from([1, 25, 50, 75, 100]),
)
@settings(max_examples=300, deadline=None)
def test_kelly_mathematical_correctness(
    win_rate: Decimal,
    win_loss_ratio: Decimal,
    kelly_frac: Decimal,
    equity: Decimal,
    entry_price: Decimal,
    lot_size: int,
) -> None:
    """Test KellySizer mathematical formula correctness."""
    from honba_strategies.components.sizers.kelly import KellySizer

    context = SizingContext(
        equity=equity,
        cash_balance=equity,
        margin_used=Decimal("0"),
        available_margin=equity,
        positions={},
    )

    signal = Signal(
        direction=1,
        entry_price=entry_price,
        stop_loss=entry_price * Decimal("0.98"),
        volatility_atr=None,
        confidence=Decimal("1"),
    )

    sizer = KellySizer(
        win_rate=win_rate,
        win_loss_ratio=win_loss_ratio,
        kelly_fraction=kelly_frac,
        max_position_notional=None,
        lot_size=Decimal(str(lot_size)),
    )

    result = sizer.calculate_size(signal, context)

    optimal_kelly = win_rate - (Decimal("1") - win_rate) / win_loss_ratio
    applied_kelly = optimal_kelly * kelly_frac

    if applied_kelly > 0:
        risk_amount = equity * applied_kelly
        stop_distance = entry_price - (entry_price * Decimal("0.98"))  # 0.02 * entry_price
        raw_qty = risk_amount / stop_distance
        expected_lots = int(raw_qty // lot_size)
        expected_qty = Decimal(str(expected_lots * lot_size))
    else:
        expected_qty = Decimal("0")

    assert abs(result.quantity - expected_qty) <= Decimal(str(lot_size))


@given(
    equity=st.decimals(min_value="10000", max_value="10000000", places=2),
    num_signals=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_equal_risk_budget_allocation(equity: Decimal, num_signals: int) -> None:
    """Test EqualRiskSizer allocates equal risk budget across signals."""
    from honba_strategies.components.sizers.equal_risk import EqualRiskSizer

    context = SizingContext(
        equity=equity,
        cash_balance=equity,
        margin_used=Decimal("0"),
        available_margin=equity,
        positions={},
    )

    signals = [
        Signal(
            direction=1,
            entry_price=Decimal("1000") + Decimal(str(i * 100)),
            stop_loss=Decimal("950") + Decimal(str(i * 100)),
            volatility_atr=Decimal("20"),
            confidence=Decimal("1"),
        )
        for i in range(num_signals)
    ]

    risk_budget_pct = Decimal("0.05")
    sizer = EqualRiskSizer(
        total_risk_pct=risk_budget_pct,
        max_position_notional=equity,
    )

    total_risk = Decimal("0")
    for sig in signals:
        result = sizer.calculate_size(sig, context, all_signals=signals)
        total_risk += result.risk_at_stake

    max_risk = equity * risk_budget_pct
    max_lot_risk = Decimal("25") * Decimal("50")
    assert total_risk <= max_risk + max_lot_risk * num_signals


@given(
    equity=st.decimals(min_value="100", max_value="1000", places=2),
    entry_price=st.decimals(min_value="1000", max_value="50000", places=2),
    lot_size=st.sampled_from([25, 50, 75, 100]),
)
@settings(max_examples=100, deadline=None)
def test_sizers_handle_insufficient_equity(
    equity: Decimal,
    entry_price: Decimal,
    lot_size: int,
) -> None:
    """Test all sizers handle insufficient equity gracefully (return 0 quantity)."""
    context = SizingContext(
        equity=equity,
        cash_balance=equity,
        margin_used=Decimal("0"),
        available_margin=equity,
        positions={},
    )

    signal = Signal(
        direction=1,
        entry_price=entry_price,
        stop_loss=entry_price * Decimal("0.98"),
        volatility_atr=Decimal("20"),
        confidence=Decimal("1"),
    )

    lot_cost = Decimal(str(lot_size)) * entry_price
    if equity < lot_cost:
        sizers = [
            FixedFractionalSizer(risk_pct=Decimal("0.01"), max_position_notional=equity, lot_size=Decimal(str(lot_size))),
            AtrVolatilitySizer(target_risk_pct=Decimal("0.015"), atr_multiplier=Decimal("2.0"), max_position_notional=equity, lot_size=Decimal(str(lot_size))),
            KellySizer(win_rate=Decimal("0.55"), win_loss_ratio=Decimal("1.5"), kelly_fraction=Decimal("0.5"), max_position_notional=equity, lot_size=Decimal(str(lot_size))),
            FixedNotionalSizer(target_notional=equity, lot_size=Decimal(str(lot_size))),
            EqualRiskSizer(total_risk_pct=Decimal("0.05"), max_position_notional=equity, lot_size=Decimal(str(lot_size))),
        ]

        for sizer in sizers:
            kwargs = {"all_signals": [signal]} if isinstance(sizer, EqualRiskSizer) else {}
            result = sizer.calculate_size(signal, context, **kwargs)
            assert result.quantity == 0, f"{sizer.__class__.__name__} should return 0 for insufficient equity"


@given(
    equity=st.decimals(min_value="10000", max_value="1000000", places=2),
    entry_price=st.decimals(min_value="100", max_value="10000", places=2),
    stop_loss=st.decimals(min_value="50", max_value="9900", places=2),
    lot_size=st.sampled_from([1, 25, 50]),
    risk_pct=st.decimals(min_value="0.01", max_value="0.1", places=3),
)
@settings(max_examples=200, deadline=None)
def test_fixed_fractional_max_notional_cap(equity: Decimal, entry_price: Decimal, stop_loss: Decimal, lot_size: int, risk_pct: Decimal) -> None:
    """Test FixedFractionalSizer respects max_position_notional cap."""
    from honba_strategies.components.sizers.fixed_fractional import FixedFractionalSizer

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

    max_notional = equity * Decimal("0.1")
    sizer = FixedFractionalSizer(
        risk_pct=risk_pct,
        max_position_notional=max_notional,
        lot_size=Decimal(str(lot_size)),
    )

    result = sizer.calculate_size(signal, context)

    assert result.notional <= max_notional
    if result.capped_by_limit:
        assert "max_position_notional" in (result.capping_reason or "")


@given(
    equity=st.decimals(min_value="10000", max_value="1000000", places=2),
    atr=st.decimals(min_value="1", max_value="1000", places=2),
    entry_price=st.decimals(min_value="100", max_value="10000", places=2),
    lot_size=st.sampled_from([1, 25, 50]),
    target_risk=st.decimals(min_value="0.01", max_value="0.05", places=3),
    atr_mult=st.decimals(min_value="1.0", max_value="3.0", places=1),
)
@settings(max_examples=200, deadline=None)
def test_atr_volatility_max_notional_cap(equity: Decimal, atr: Decimal, entry_price: Decimal, lot_size: int, target_risk: Decimal, atr_mult: Decimal) -> None:
    """Test AtrVolatilitySizer respects max_position_notional cap."""
    from honba_strategies.components.sizers.volatility import AtrVolatilitySizer

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

    max_notional = equity * Decimal("0.1")
    sizer = AtrVolatilitySizer(
        target_risk_pct=target_risk,
        atr_multiplier=atr_mult,
        max_position_notional=max_notional,
        lot_size=Decimal(str(lot_size)),
    )

    result = sizer.calculate_size(signal, context)

    assert result.notional <= max_notional
    if result.capped_by_limit:
        assert "max_position_notional" in (result.capping_reason or "")


@given(
    equity=st.decimals(min_value="10000", max_value="1000000", places=2),
    entry_price=st.decimals(min_value="100", max_value="10000", places=2),
    lot_size=st.sampled_from([1, 25, 50]),
)
@settings(max_examples=200, deadline=None)
def test_fixed_notional_never_exceeds_target(equity: Decimal, entry_price: Decimal, lot_size: int) -> None:
    """Test FixedNotionalSizer never exceeds target notional."""
    from honba_strategies.components.sizers.fixed_notional import FixedNotionalSizer

    context = SizingContext(
        equity=equity,
        cash_balance=equity,
        margin_used=Decimal("0"),
        available_margin=equity,
        positions={},
        current_price=entry_price,
    )

    target_notional = equity * Decimal("0.2")
    signal = Signal(
        direction=1,
        entry_price=entry_price,
        stop_loss=None,
        volatility_atr=None,
        confidence=Decimal("1"),
    )

    sizer = FixedNotionalSizer(
        target_notional=target_notional,
        lot_size=Decimal(str(lot_size)),
    )

    result = sizer.calculate_size(signal, context)

    assert result.notional <= target_notional + Decimal(str(lot_size)) * entry_price
    assert result.notional >= target_notional - Decimal(str(lot_size)) * entry_price


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])