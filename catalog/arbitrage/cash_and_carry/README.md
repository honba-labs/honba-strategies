# Cash-and-Carry Basis Arbitrage Strategy

## Usage

```python
from honba_strategies.arbitrage import CashAndCarryStrategy, CashAndCarryConfig
from decimal import Decimal

config = CashAndCarryConfig(
    spot_symbol="RELIANCE",
    futures_symbol="RELIANCE",
    futures_expiry="2026-12-25",
    min_basis_bps=Decimal("50"),
    lot_size=250,
)
strategy = CashAndCarryStrategy(config)
```

## Possible output

```
Running Cash-and-Carry arbitrage...
Fair basis: 45.2 bps, Actual: 62.1 bps
Entry: Long RELIANCE spot (CNC), Short RELIANCE DEC futures
```

## Pitfalls

- Futures expiry mismatch can leave unwanted directional exposure.
- Corporate actions (dividends, splits) affect fair basis calculation.
- Liquidity drought in near-month futures can widen basis unpredictably.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.