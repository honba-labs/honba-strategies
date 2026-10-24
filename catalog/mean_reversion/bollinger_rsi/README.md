# Bollinger Band + RSI Exhaustion Strategy

## Usage

```python
from honba_strategies.mean_reversion import BollingerRsiStrategy, BollingerRsiConfig
from decimal import Decimal

config = BollingerRsiConfig(
    bb_period=20,
    bb_std_dev=Decimal("2.0"),
    rsi_period=14,
    rsi_oversold=Decimal("25"),
    rsi_overbought=Decimal("75"),
)
strategy = BollingerRsiStrategy(config)
```

## Possible output

```
Running Bollinger Band + RSI Mean Reversion...
BB: Upper=2550, Middle=2500, Lower=2450
RSI: 22 (Oversold)
Price: 2448 (Below Lower Band)
Entry: Long RELIANCE @ 2448
```

## Pitfalls

- Bollinger bands widen in volatile markets; false signals increase
- RSI can remain oversold in strong trends; confirm with price action
- Mean reversion strategies can suffer in strong trending markets
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.