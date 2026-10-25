# BankNifty Iron Condor Strategy

## Usage

```python
from decimal import Decimal
from honba_strategies.options import IronCondorConfig, IronCondorStrategy

config = IronCondorConfig(
    name="banknifty_iron_condor",
    symbol="BANKNIFTY",
    exchange="NFO",
    capital=Decimal("1000000"),
    entry_time="09:25",
    exit_time="15:10",
    wing_width=200,
    short_delta=Decimal("0.16"),
    profit_target_pct=Decimal("0.50"),
    adjustment_delta=Decimal("0.30"),
    lots=1,
)

strategy = IronCondorStrategy(config)
```

## Possible output

The strategy emits signals for the 4-leg iron condor structure with direction, entry price, stop-loss, and ATR.
Typical signal: `{"direction": 1, "entry_price": 48000, "stop_loss": 48500, "volatility_atr": 400}`.
Positions are managed with delta-neutral adjustments and early profit taking at 50%.

## Pitfalls

- Defined risk but max loss = wing_width - credit received - can be substantial. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- Theta decay accelerates near expiry - best held 7-14 days
- Adjustment risk: rolling wings can lock in losses if market reverses
- BANKNIFTY wider spreads than NIFTY - higher slippage on 4-leg entry
- Correlated legs: all 4 options move together in strong trends