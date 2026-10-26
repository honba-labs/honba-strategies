# TWAP Execution Strategy

Multi-version catalog entry for TWAP (Time-Weighted Average Price) execution.

## Differences between v1 and v2

- **v1 (`catalog/execution/twap/v1`)**:
  - Implements Strategy API v1 (`honba.v1.Strategy`, `__strategy_api_version__ = "1.0.0"`).
  - Uses the classic lifecycle hooks (`on_bar(bar, ctx)`).
  - Preserved for backwards compatibility with existing pipelines and backtests.
- **v2 (`catalog/execution/twap/v2`)**:
  - Implements Strategy API v2 (`honba.v2.Strategy`, `__strategy_api_version__ = "2.0.0"`).
  - Unified event-driven hook `on_step(event, ctx)` with automatic bar unpacking.
  - Latest and recommended for new development.

## Usage

```python
from honba.strategies.loader import load_named

# New software loads latest recommended version (v2.0.0)
strat_latest = load_named("twap")

# Existing software continues to load v1 without breaking
strat_v1 = load_named("twap", version="1.2.0")

# SemVer range resolution for existing pipelines
strat_v1_compatible = load_named("twap", version="^1.0.0")
```

## Possible output

```
Running TWAP execution...
Divides parent order into time-based slices with randomized jitter.
```

## Pitfalls

- Large parent orders may still impact market if duration is too short.
- Jitter helps avoid detection but adds execution uncertainty.
- SEBI freeze limits must be respected per exchange rules.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.
