# supertrend_follow

Long-only Supertrend trend follower for NSE cash equities. Buy while the Supertrend is
in an uptrend and flat; exit fully when it flips to a downtrend.

- **Category:** momentum / trend
- **Indicators** (`[indicators.trend]` in `config.toml`): `supertrend` (`atr_period`, `factor`), built through `IndicatorBank`
- **Params:** `capital`, `allocation` (whole-share sizing)
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy

Change the indicator or its parameters in `config.toml` without touching code.

Test: `pytest momentum/trend/supertrend_follow` (needs `honba` on the path).
