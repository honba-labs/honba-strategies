# VWAP Execution Strategy

**Status: scaffold**

## Usage

```python
from honba.strategies.config import StrategyConfig
from honba.strategies.loader import load_named

VwapStrategy, config = load_named("vwap")
# Configure via config.toml or override params
```

## Possible output

```
Running VWAP execution...
```

## Pitfalls

- Requires accurate historical volume profile for the instrument.
- Participation rate too high increases market impact.
- Volume droughts can cause execution to stall.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.