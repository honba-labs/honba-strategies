# Fixed Notional Position Sizer

## Usage

```python
from decimal import Decimal
from honba_strategies.components.sizers import FixedNotionalSizer
from honba_strategies.components.sizers.base import Signal, SizingContext
from honba.entities.instrument import InstrumentId

sizer = FixedNotionalSizer(
    target_notional=Decimal("100000"),
    max_position_notional=Decimal("100000"),
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
print(f"Quantity: {result.quantity}, Notional: {result.notional}")
```

## Possible output

Returns `PositionSizingResult` with fixed notional position size.

Example: `PositionSizingResult(quantity=Decimal('0'), notional=Decimal('0'), risk_at_stake=Decimal('0'), capped_by_limit=False, capping_reason='flat_signal', stop_distance=None, lot_size=Decimal('25'))`

The result includes all sizing details needed for downstream execution steps.

## Pitfalls

- Ignores volatility and stop-loss - risk per trade varies widely. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- Fixed notional can exceed freeze limits for low-priced instruments
- No risk management - a 10% move on 1L notional = 10K loss
- Not suitable for leveraged instruments without additional risk guards
- Does not scale with account equity - manual adjustment needed as account grows