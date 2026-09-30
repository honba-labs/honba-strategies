# macd_trend

Long-only MACD trend follower. Buy when MACD is above its signal line and the close is above the trend EMA; exit fully when MACD is below signal and the close is below the EMA.

- **Category:** 01_momentum
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `ema`, `fastperiod`, `slowperiod`, `signal`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest 01_momentum/macd_trend` (needs `honba` on the path).
