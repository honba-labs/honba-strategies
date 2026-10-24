# Basket Arbitrage Strategy (ETF vs Synthetic Basket)

## Usage

```python
from honba_strategies.arbitrage import BasketArbitrageStrategy, BasketConfig
from decimal import Decimal

config = BasketConfig(
    etf_symbol="NIFTYBEES",
    min_basis_bps=Decimal("10"),
    rebalance_threshold_bps=Decimal("5"),
)
strategy = BasketArbitrageStrategy(config)
```

## Possible output

```
Running Basket Arbitrage...
Synthetic basket: 21545.3, ETF: 21568.7
Basis: 10.9 bps (> 10 bps threshold)
Entry: Sell NIFTYBEES, Buy synthetic basket (50 constituents)
```

## Pitfalls

- ETF tracking error and NAV discount/premium can create persistent basis.
- Constituent liquidity varies; illiquid names create execution risk.
- Corporate actions (index rebalancing) require weight updates.
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.