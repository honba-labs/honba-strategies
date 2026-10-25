# ATR Volatility Position Sizer

## Usage

```python
from decimal import Decimal
from honba_strategies.components.sizers import AtrVolatilitySizer
from honba_strategies.components.sizers.base import Signal, SizingContext
from honba.entities.instrument import InstrumentId

sizer = AtrVolatilitySizer(
    target_risk_pct=Decimal("0.015"),
    atr_multiplier=Decimal("2.0"),
    max_position_notional=Decimal("500000"),
    lot_size=Decimal("25"),
    freeze_limit=1800,
)

signal = Signal(direction=1, entry_price=Decimal("24000"), volatility_atr=Decimal("300"))
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
print(f"Quantity: {result.quantity}, Notional: {result.notional}, Risk: {result.risk_at_stake}")
```

## Possible output

Returns `PositionSizingResult` with ATR-based position size.

Example: `PositionSizingResult(quantity=Decimal('25'), notional=Decimal('600000'), risk_at_stake=Decimal('15000'), capped_by_limit=False, capping_reason=None, stop_distance=Decimal('600'), lot_size=Decimal('25'))`

The result includes all sizing details needed for downstream execution steps.

## Pitfalls

- Requires ATR from market data; fails silently if unavailable. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- Volatility targeting mode assumes constant correlation - may underestimate risk in crises
- Inverse vol sizing can lead to large positions in low-vol regimes
- ATR is backward-looking; sudden regime changes not captured