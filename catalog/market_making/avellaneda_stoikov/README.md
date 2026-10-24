# Avellaneda-Stoikov Market Maker

## Usage

```python
from honba_strategies.market_making import AvellanedaStoikovStrategy, AvellanedaStoikovConfig
from decimal import Decimal

config = AvellanedaStoikovConfig(
    symbol="RELIANCE",
    gamma=Decimal("0.1"),
    sigma=Decimal("0.02"),
    kappa=Decimal("1.5"),
    quote_quantity=Decimal("100"),
)
strategy = AvellanedaStoikovStrategy(config)
```

## Possible output

```
Running Avellaneda-Stoikov MM...
Mid: 2500.25, Inventory: 50
Reservation: 2498.50, Half-spread: 1.25
Bid: 2497.25, Ask: 2499.75
```

## Pitfalls

- Model assumes Brownian motion; real markets have jumps and fat tails
- Requires accurate volatility estimation; wrong sigma leads to adverse skew
- Inventory risk accumulates in trending markets; hard stops needed
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.