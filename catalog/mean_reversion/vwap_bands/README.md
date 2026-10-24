# VWAP Band Reversion Strategy

## Usage

```python
from honba_strategies.mean_reversion import VwapBandReversionStrategy, VwapBandConfig
from decimal import Decimal

config = VwapBandConfig(
    std_dev_mult=Decimal("2.5"),
    entry_cutoff="15:00",
    square_off="15:20",
)
strategy = VwapBandReversionStrategy(config)
```

## Possible output

```
Running VWAP Band Reversion...
VWAP: 2500.00, Upper: 2531.25, Lower: 2468.75
Price: 2465.00 (Below Lower Band)
Entry: Long RELIANCE @ 2465.00
```

## Pitfalls

- VWAP bands can widen in low volume periods; false signals increase
- Entry cutoff at 15:00 may miss late-day reversals
- Strict 15:20 square-off may exit prematurely in strong trends
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.