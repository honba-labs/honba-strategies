# Iceberg Execution Strategy

**Status: scaffold**

## Usage

```python
from honba.strategies.config import StrategyConfig
from honba.strategies.loader import load_named

IcebergStrategy, config = load_named("iceberg")
# Configure via config.toml or override params
```

## Possible output

```
Running Iceberg execution...
```

## Pitfalls

- Hidden reserve not visible to market; may execute slower than expected.
- Randomized display size helps avoid detection but adds uncertainty.
- Requires sufficient hidden reserve to maintain iceberg structure.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.