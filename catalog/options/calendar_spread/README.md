# Calendar Spread Strategy

## Usage

```python
from decimal import Decimal
from honba_strategies.options import CalendarSpreadConfig, CalendarSpreadStrategy

config = CalendarSpreadConfig(
    name="calendar_spread",
    symbol="NIFTY",
    exchange="NFO",
    capital=Decimal("1000000"),
    strike_selection="atm",
    near_expiry_days=7,
    far_expiry_days=35,
    profit_target_pct=Decimal("0.25"),
    stop_loss_pct=Decimal("0.50"),
    lots=1,
)

strategy = CalendarSpreadStrategy(config)
```

## Possible output

The strategy emits signals for the calendar spread with direction, entry price, stop-loss, and ATR.
Typical signal: `{"direction": 1, "entry_price": 24000, "stop_loss": 23800, "volatility_atr": 300}`.
Spreads are exited at 25% profit target or 50% stop-loss, managed before near-term expiry gamma risk.

## Pitfalls

- Requires positive theta (far-term IV > near-term IV) - check term structure. See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
- Vega risk: long far-term option loses if IV drops across term structure
- Gamma risk near near-term expiry - manage actively in last week
- Assignment risk on short near-term option if ITM
- Wide bid-ask on far-term options increases entry cost