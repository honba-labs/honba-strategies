# Risk Parity Allocation

## Usage

```python
from honba_strategies.portfolio import RiskParityStrategy, RiskParityConfig

config = RiskParityConfig(lookback_window=60)
strategy = RiskParityStrategy(config)
```

## Possible output

```
Running Risk Parity Allocation...
Calculated volatilities for 10 assets
Risk parity weights computed (inverse volatility)
Rebalanced portfolio with equal risk contribution
```

## Pitfalls

- Assumes stable volatility relationships
- May underperform in momentum-driven markets
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.
