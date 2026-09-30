# turtle_20

Simplified Turtle System 1, long-only, no pyramiding. Buy a break of the previous `entry`-bar high; exit on a close below the previous `exit`-bar low or a 2 x ATR protective stop.

- **Category:** momentum / trend
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `entry`, `exit`, `atr_period`, `atr_mult`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/trend/turtle_20` (needs `honba` on the path).
