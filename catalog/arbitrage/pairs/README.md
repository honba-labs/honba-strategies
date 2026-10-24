# Statistical Pairs Trading Strategy

## Usage

```python
from honba_strategies.arbitrage import PairsTradingStrategy, PairsConfig
from decimal import Decimal

config = PairsConfig(
    leg_a_symbol="HDFCBANK",
    leg_b_symbol="ICICIBANK",
    entry_zscore=Decimal("2.0"),
    exit_zscore=Decimal("0.0"),
    stoploss_zscore=Decimal("3.5"),
)
strategy = PairsTradingStrategy(config)
```

## Possible output

```
Running Pairs Trading strategy...
Cointegration validated: HDFCBANK vs ICICIBANK (beta=0.95, alpha=0.02)
Entry signal: Z-score = 2.15 (> 2.0), spreading HDFCBANK/ICICIBANK
```

## Pitfalls

- Cointegration can break down during regime changes; validate out-of-sample.
- Z-score thresholds are sensitive; optimize walk-forward.
- Leg execution risk: if one leg fills and the other doesn't, directional exposure remains.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.