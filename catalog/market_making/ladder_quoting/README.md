# Ladder Quoting Strategy

## Usage

```python
from honba_strategies.market_making import LadderQuotingStrategy, LadderQuotingConfig
from decimal import Decimal

config = LadderQuotingConfig(
    symbol="RELIANCE",
    num_levels=5,
    level_spread_bps=Decimal("5"),
    base_quantity=Decimal("100"),
)
strategy = LadderQuotingStrategy(config)
```

## Possible output

```
Running Ladder Quoting...
Mid: 2500.25, Levels: 3
Bid Ladder: 2500.00 @ 100, 2499.87 @ 50, 2499.75 @ 25
Ask Ladder: 2500.50 @ 100, 2500.63 @ 50, 2500.75 @ 25
```

## Pitfalls

- Inventory can accumulate rapidly in trending markets
- Geometric decay may not match optimal inventory distribution
- Requires frequent rebalancing in volatile markets
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.