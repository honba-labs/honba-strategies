# KAMA Crossover Strategy

## Usage

```python
from honba_strategies.trend import KamaCrossoverStrategy, KamaConfig
from decimal import Decimal

config = KamaConfig(
    fast_period=10,
    slow_period=30,
    er_period=10,
    risk_per_trade_pct=Decimal("0.02"),
)
strategy = KamaCrossoverStrategy(config)
```

## Possible output

```
Running KAMA Crossover...
Fast KAMA: 2500.50, Slow KAMA: 2498.20
Golden Cross: Fast crossed above Slow
Entry: Long RELIANCE @ 2501.00
```

## Pitfalls

- KAMA can lag during strong trends; fast/slow period choice is critical
- Efficiency Ratio can be noisy on short timeframes; use appropriate ER period
- Crossover signals can be late in fast-moving markets
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.