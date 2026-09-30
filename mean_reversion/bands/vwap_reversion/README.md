# vwap_reversion

Intraday long-only mean reversion to the session VWAP for NSE, in IST. Buy when the close is
below the lower VWAP band before `entry_cutoff`; exit at VWAP or at `squareoff`. Nothing is
carried overnight.

- **Category:** mean reversion / bands
- **Indicators** (`[indicators.vwap]`): `vwap` (`band_mult`), reset on each IST session day
- **Params:** `capital`, `allocation`, `entry_cutoff`, `squareoff` (HH:MM IST)
- **Costs:** applied by the Honba backtest engine (intraday STT, GST, stamp duty), not the strategy
- **Bars:** intraday (e.g. 5-minute) bars with volume

Test: `pytest mean_reversion/bands/vwap_reversion` (needs `honba` on the path).
