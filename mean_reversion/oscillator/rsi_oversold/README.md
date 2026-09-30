# rsi_oversold

Long-only daily mean reversion. Buy an oversold dip (RSI below `entry`) while the close is above the trend SMA; exit when RSI recovers above `exit` or after `max_hold` bars.

- **Category:** mean reversion / oscillator
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `rsi_period`, `entry`, `exit`, `trend_sma`, `max_hold`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest mean_reversion/oscillator/rsi_oversold` (needs `honba` on the path).
