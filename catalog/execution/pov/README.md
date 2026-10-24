# POV Execution Strategy

**Status: scaffold**

## Usage

```python
from honba.strategies.config import StrategyConfig
from honba.strategies.loader import load_named

PovStrategy, config = load_named("pov")
# Configure via config.toml or override params
```

## Possible output

```
Running POV execution...
```

## Pitfalls

- Low liquidity can cause execution to stall indefinitely.
- High participation rate increases market impact risk.
- Volume spikes may cause oversized slices if not capped.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.