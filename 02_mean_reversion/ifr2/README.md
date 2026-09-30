# ifr2

Long-only RSI(2) dip buying above the Ichimoku cloud; exit when the close clears the highs of the two previous bars. The original's Hilbert trend-mode filter is dropped.

- **Category:** 02_mean_reversion
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `oversold`, `tenkan`, `kijun`, `senkou_b`, `displacement`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest 02_mean_reversion/ifr2` (needs `honba` on the path).
