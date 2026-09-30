# sma_crossover

Long-only SMA crossover for NSE cash equities. Buy when the fast SMA is above
the slow SMA while flat; exit fully when it drops below.

- **Category:** momentum / trend following
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `fast`, `slow`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Inspired by:** the classic golden-cross idea; ported from a Jesse example

Test: `pytest 01_momentum/sma_crossover` (needs `honba` on the path).
