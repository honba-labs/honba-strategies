# Portfolio

Multi-instrument strategies built on the composable portfolio-construction layer in
`honba.strategies.portfolio`. A portfolio strategy is assembled from four parts: a universe
(which instruments are eligible), a selector (which of them to hold), a weighting scheme
(how much of each) and a rebalance schedule (when). The catalog entry binds those parts to a
`config.toml`; the logic lives in the core.

| Sub-category | What it holds |
| :--- | :--- |
| [`rebalancing/`](rebalancing/README.md) | Hold a universe and periodically restore target weights. |

Each strategy directory has the standard files: `strategy.py`, `config.toml`, `README.md`,
`tests/` and `backtest_result.json`.

## Params grammar

```toml
[params]
universe   = "nifty200_alpha30"   # engine-known name, or a list of "SYMBOL[:EXCHANGE]"
weighting  = "equal"              # "equal" | "inverse_vol[:lookback]"
schedule   = "every:15d"          # "every:<N>d" | "monthly:first_session" | "drift:<x>" (join with +)
select     = "top:10:momentum:126"  # optional; omitted keeps every member
allocation = 0.995                # fraction of portfolio value to deploy, in (0, 1]
```

Unknown keys and malformed values raise `ValueError`. See `honba.strategies.portfolio.factory`.
