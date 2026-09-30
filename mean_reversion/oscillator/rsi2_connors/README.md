# rsi2_connors

Long-only RSI(2) mean reversion. Buy RSI(2) <= `oversold` while above the trend SMA; exit once the close is above the short exit SMA. Frequent signals by design.

- **Category:** mean reversion / oscillator
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `oversold`, `trend_sma`, `exit_sma`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest mean_reversion/oscillator/rsi2_connors` (needs `honba` on the path).
