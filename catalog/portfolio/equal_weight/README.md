# Equal Weight & Periodic Rebalancer

## Usage

```python
from honba_strategies.portfolio import EqualWeightRebalancer, EqualWeightConfig
from decimal import Decimal

config = EqualWeightConfig(
    drift_threshold=Decimal("0.05"),
    rebalance_frequency="daily",
    max_positions=10,
)
strategy = EqualWeightRebalancer(config)
```

## Pitfalls

- Frequent rebalancing increases transaction costs in illiquid markets
- Equal weighting ignores diversification benefits across asset classes
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.
