# TWAP Execution Strategy (v1)

**Status: active**

## Usage

```python
from honba.strategies.loader import load_named

# Preserved for existing software (honba.v1.Strategy)
TwapStrategy, config = load_named("twap", version="1.2.0")
```

## Possible output

```
Running TWAP execution v1 (honba.v1.Strategy)...
Emitting child slice orders over duration window.
```

## Pitfalls

- Large parent orders may still impact market if duration is too short.
- Jitter helps avoid detection but adds execution uncertainty.
- SEBI freeze limits must be respected per exchange rules.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.
