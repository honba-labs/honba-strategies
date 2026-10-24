# TWAP Execution Strategy

**Status: scaffold**

## Usage

```python
from honba.strategies.config import StrategyConfig
from honba.strategies.loader import load_named

TwapStrategy, config = load_named("twap")
# Configure via config.toml or override params
```

## Possible output

```
Running TWAP execution...
```

## Pitfalls

- Large parent orders may still impact market if duration is too short.
- Jitter helps avoid detection but adds execution uncertainty.
- SEBI freeze limits must be respected per exchange rules.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.