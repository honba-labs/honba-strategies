# bollinger_breakout

Long-only Bollinger breakout. Buy a close above the upper band (hl2 source) while above the Ichimoku cloud; exit fully on a close below the middle band.

- **Category:** momentum / breakout
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `period`, `mult`, `tenkan`, `kijun`, `senkou_b`, `displacement`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/breakout/bollinger_breakout` (needs `honba` on the path).
