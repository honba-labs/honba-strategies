# Equal Risk Contribution Position Sizer

## Usage

```python
from decimal import Decimal
from honba_strategies.components.sizers import EqualRiskSizer
from honba_strategies.components.sizers.base import Signal, SizingContext
from honba.entities.instrument import InstrumentId

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

corr_matrix = [
    [Decimal("1.0"), Decimal("0.3")],
    [Decimal("0.3"), Decimal("1.0")],
]

context = SizingContext(equity=Decimal("1000000"), cash_balance=Decimal("800000"),
                       margin_used=Decimal("0"), available_margin=Decimal("800000"))

for signal in signals:
    result = sizer.calculate_size(signal, context, all_signals=signals, correlation_matrix=corr_matrix)
    print(f"Quantity: {result.quantity}, Risk: {result.risk_at_stake}")
```

## Possible output

Returns `PositionSizingResult` with equal-risk position sizes across all signals.

Example: `PositionSizingResult(quantity=Decimal('75'), notional=Decimal('1800000'), risk_at_stake=Decimal('22500'), capped_by_limit=False, capping_reason=None, stop_distance=Decimal('300'), lot_size=Decimal('25'))`

The result includes all sizing details needed for downstream execution steps.

## Pitfalls

- Requires all active signals for multi-signal ERC - single signal mode uses full budget. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- Correlation matrix must be provided externally - estimation is complex
- Assumes correlations are stable - regime changes break ERC assumptions
- Equal risk budget may underweight high-conviction signals
- Correlation adjustment can amplify positions in negatively correlated assets