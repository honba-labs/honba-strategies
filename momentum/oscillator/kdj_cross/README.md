# kdj_cross

Long-only KDJ momentum. Buy when J is above both K and D; exit when in profit and J turns down, when J drops below K or D, or on a 2 x ATR protective stop. Jesse's `J > (K and D)` only compared J with D; the intended J > K and J > D is used here.

- **Category:** momentum / oscillator
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `fastk`, `slowk`, `slowd`, `atr_period`, `atr_mult`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/oscillator/kdj_cross` (needs `honba` on the path).
