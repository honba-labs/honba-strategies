# Fixed Fractional Position Sizer

## Usage

```python
from decimal import Decimal
from honba_strategies.components.sizers import FixedFractionalSizer
from honba_strategies.components.sizers.base import Signal, SizingContext
from honba.entities.instrument import InstrumentId

sizer = FixedFractionalSizer(
    risk_pct=Decimal("0.01"),
    max_position_notional=Decimal("500000"),
    lot_size=Decimal("25"),
    freeze_limit=1800,
)

signal = Signal(direction=1, entry_price=Decimal("24000"), stop_loss=Decimal("23700"))
context = SizingContext(
    equity=Decimal("1000000"),
    cash_balance=Decimal("800000"),
    margin_used=Decimal("200000"),
    available_margin=Decimal("600000"),
    instrument_id=InstrumentId("NIFTY50", "NFO"),
    current_price=Decimal("24000"),
)

result = sizer.calculate_size(signal, context)
print(f"Quantity: {result.quantity}, Notional: {result.notional}, Risk: {result.risk_at_stake}")
```

## Possible output

Returns `PositionSizingResult` with discretized quantity, notional, and risk at stake.

Example: `PositionSizingResult(quantity=Decimal('25'), notional=Decimal('600000'), risk_at_stake=Decimal('7500'), capped_by_limit=False, capping_reason=None, stop_distance=Decimal('300'), lot_size=Decimal('25'))`

The result includes all sizing details needed for downstream execution steps.

## Pitfalls

- Requires signals with explicit stop-loss levels; uses ATR fallback otherwise. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- Position size scales linearly with equity - large accounts may hit freeze limits
- Does not account for correlation between concurrent signals
- Fixed risk % can lead to overtrading in low-volatility regimes