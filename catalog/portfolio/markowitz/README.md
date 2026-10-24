# Markowitz Mean-Variance Optimizer

## Usage

```python
from honba_strategies.portfolio import MarkowitzStrategy, MarkowitzConfig

config = MarkowitzConfig(max_weight=0.20)
strategy = MarkowitzStrategy(config)
```

## Possible output

```
Running Markowitz Mean-Variance Optimization...
Optimized portfolio for maximum Sharpe ratio
Portfolio weights with max position constraints applied
```

## Pitfalls

- Requires stable covariance estimates
- Sensitive to estimation error
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.
