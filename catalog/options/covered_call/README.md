# Covered Call Strategy

## Usage

```python
from decimal import Decimal
from honba_strategies.options import CoveredCallConfig, CoveredCallStrategy

config = CoveredCallConfig(
    name="covered_call",
    symbol="RELIANCE",
    exchange="NSE",
    capital=Decimal("1000000"),
    otm_pct=Decimal("0.05"),
    roll_days_before_expiry=2,
    min_premium_yield=Decimal("0.01"),
    max_assignment_risk=Decimal("0.30"),
    quantity=100,
)

strategy = CoveredCallStrategy(config)
```

## Possible output

The strategy emits signals for covered call writing with direction, entry price, stop-loss, and ATR.
Typical signal: `{"direction": 1, "entry_price": 2500, "stop_loss": 2400, "volatility_atr": 50}`.
Calls are rolled before expiry, with assignment risk monitored via delta threshold.

## Pitfalls

- Assignment risk: stock called away at strike, missing upside. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- Dividend capture requires holding through ex-date - market risk
- Rolling calls incurs transaction costs and potential slippage
- CNC delivery requires full capital - no leverage
- Opportunity cost: capital tied up in stock could be deployed elsewhere