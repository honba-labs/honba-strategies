# Passive Spread Quoting Strategy

## Usage

```python
from honba_strategies.market_making import SpreadQuotingStrategy, SpreadQuotingConfig
from decimal import Decimal

config = SpreadQuotingConfig(
    symbol="RELIANCE",
    spread_bps=Decimal("10"),
    quote_quantity=Decimal("100"),
    obi_threshold=Decimal("0.3"),
)
strategy = SpreadQuotingStrategy(config)
```

## Possible output

```
Running Spread Quoting strategy...
OBI: 0.15 (within threshold 0.3)
Bid: 2500.00 @ 100, Ask: 2500.50 @ 100
```

## Pitfalls

- Adverse selection risk when OBI signal is weak or delayed
- Inventory can accumulate rapidly in trending markets
- Requires low-latency market data feed for effective quoting
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.