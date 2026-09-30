# donchian_trend

Long-only Donchian breakout. Buy a close above the previous N-bar high while above the trend SMA; exit fully on a close below the previous N-bar low.

- **Category:** momentum / trend
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `period`, `trend_sma`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/trend/donchian_trend` (needs `honba` on the path).
