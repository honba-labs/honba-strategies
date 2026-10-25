# Kelly Criterion Position Sizer

## Usage

```python
from decimal import Decimal
from honba_strategies.components.sizers import KellySizer
from honba_strategies.components.sizers.base import Signal, SizingContext
from honba.entities.instrument import InstrumentId

sizer = KellySizer(
    win_rate=Decimal("0.55"),
    win_loss_ratio=Decimal("1.5"),
    kelly_fraction=Decimal("0.5"),
    max_position_notional=Decimal("500000"),
    lot_size=Decimal("25"),
    freeze_limit=1800,
)

signal = Signal(direction=1, entry_price=Decimal("24000"), stop_loss=Decimal("23700"),
                metadata={"win_rate": "0.60", "win_loss_ratio": "2.0"})
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

Returns `PositionSizingResult` with Kelly-optimal position size.

Example: `PositionSizingResult(quantity=Decimal('400'), notional=Decimal('9600000'), risk_at_stake=Decimal('120000'), capped_by_limit=True, capping_reason='max_position_notional_500000', stop_distance=Decimal('300'), lot_size=Decimal('25'))`

The result includes all sizing details needed for downstream execution steps.

## Pitfalls

- Requires accurate win-rate and win/loss estimates - garbage in, garbage out. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- Full Kelly (fraction=1.0) is extremely aggressive - use Half-Kelly (0.5) or less
- Assumes stationary win/loss distribution - regime changes break estimates
- Does not account for correlation between concurrent strategies
- Kelly fraction > 1 can occur with high win-rate + high win/loss - capped by max_kelly_fraction