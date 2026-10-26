# TWAP Execution Strategy (v2)

**Status: active**

## Usage

```python
from honba.strategies.loader import load_named

# Latest & Recommended (honba.v2.Strategy)
TwapStrategy, config = load_named("twap")
```

## Possible output

```
Running TWAP execution v2 (honba.v2.Strategy)...
Dispatching market events to on_step / on_bar.
```

## Pitfalls

- Large parent orders may still impact market if duration is too short.
- Jitter helps avoid detection but adds execution uncertainty.
- SEBI freeze limits must be respected per exchange rules.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.
