# Alpha Factor Portfolio (Top 30)

## Usage

```python
from honba_strategies.portfolio import AlphaFactorStrategy, AlphaFactorConfig

config = AlphaFactorConfig(top_n=30)
strategy = AlphaFactorStrategy(config)
```

## Possible output

```
Running Alpha Factor Portfolio...
Scored universe with Momentum, Low Vol, Quality, Value factors
Selected top 30 stocks by composite score
Constructed equally-weighted portfolio
```

## Pitfalls

- Factor premia can be cyclical
- Requires quality fundamental data
- See [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html) for general pitfalls.
