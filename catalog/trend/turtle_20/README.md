# Turtle Trading System (Richard Dennis)

## Usage

```python
from honba_strategies.trend import TurtleStrategy, TurtleConfig
from decimal import Decimal

config = TurtleConfig(
    system=1,  # 1 = 20-day, 2 = 55-day
    atr_period=20,
    atr_multiplier=Decimal("2.0"),
    pyramid_threshold=Decimal("0.5"),
    max_units=4,
    risk_per_trade_pct=Decimal("0.02"),
)
strategy = TurtleStrategy(config)
```

## Possible output

```
Running Turtle System 1 (20-day)...
Channel: 2500-2600, ATR: 12.5, N: 25.0
Long entry: 2601.0 (breakout above 2600)
Unit 1: 400 shares @ 2601.0
Pyramid: Unit 2 @ 2613.5 (+0.5N)
Stop: 2551.0 (-2N from entry)
```

## Pitfalls

- Whipsaws in sideways markets; Donchian channels generate false breakouts
- Pyramiding increases risk; max 4 units can accumulate significant exposure
- ATR-based stops can be wide in volatile markets; ensure adequate capital
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.