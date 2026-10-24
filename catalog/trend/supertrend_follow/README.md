# Supertrend Trend Following Strategy

## Usage

```python
from honba_strategies.trend import SupertrendStrategy, SupertrendConfig
from decimal import Decimal

config = SupertrendConfig(
    atr_period=10,
    multiplier=Decimal("3.0"),
    trend_timeframe="1h",
    entry_timeframe="5m",
)
strategy = SupertrendStrategy(config)
```

## Possible output

```
Running Supertrend...
ATR: 12.50, Multiplier: 3.0
Supertrend: 2487.50 (UPTREND)
Entry: Long RELIANCE @ 2501.00
```

## Pitfalls

- Supertrend can whipsaw in choppy markets; use appropriate multiplier
- ATR-based stops can be wide; requires sufficient capital
- Multi-timeframe confirmation can delay entries; tune timeframes carefully
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.