# Ornstein-Uhlenbeck Mean Reversion Strategy

## Usage

```python
from honba_strategies.mean_reversion import OuMeanReversionStrategy, OuConfig
from decimal import Decimal

config = OuConfig(
    lookback_window=60,
    entry_zscore=Decimal("2.0"),
    exit_zscore=Decimal("0.0"),
    stoploss_zscore=Decimal("3.0"),
    max_half_life_days=5,
)
strategy = OuMeanReversionStrategy(config)
```

## Possible output

```
Running OU Mean Reversion...
OU params: theta=0.15, mu=2500, sigma=15.2, half_life=4.6 days
Z-score: -2.1 (Entry threshold: -2.0)
Entry: Long RELIANCE @ 2490
```

## Pitfalls

- OU model assumes mean-reverting process; breaks down in trending regimes
- Half-life estimation can be noisy; requires sufficient lookback window
- Parameter estimation is sensitive to lookback window choice
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.