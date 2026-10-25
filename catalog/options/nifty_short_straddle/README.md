# NIFTY Short Straddle Strategy

## Usage

```python
from decimal import Decimal
from honba_strategies.options import ShortStraddleConfig, ShortStraddleStrategy

config = ShortStraddleConfig(
    name="nifty_short_straddle",
    symbol="NIFTY",
    exchange="NFO",
    capital=Decimal("1000000"),
    entry_time="09:20",
    exit_time="15:15",
    sl_pct_per_leg=Decimal("0.25"),
    combined_sl_pct=Decimal("0.20"),
    profit_target_pct=Decimal("0.50"),
    lots=1,
)

strategy = ShortStraddleStrategy(config)
```

## Possible output

The strategy emits signals with direction, entry price, stop-loss, and ATR for position sizing.
Typical signal: `{"direction": 0, "entry_price": 24000, "stop_loss": 23700, "volatility_atr": 300}`.
After entry, the straddle is managed until exit time, profit target, or stop-loss.

## Pitfalls

- Short straddle has unlimited risk on both sides - stop-loss is critical. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- High gamma risk near expiry - avoid last 2 days unless hedging actively
- IV crush after events can cause rapid losses even with correct direction
- Requires liquid option chains - wide spreads increase slippage
- Assignment risk on short options near expiry - monitor ITM probability