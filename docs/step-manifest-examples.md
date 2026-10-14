# Step manifest examples

Two chains, written as TOML. Each `[[steps]]` entry names a step `id` and may carry `with`
(param overrides, checked against the step's declared params) and `report` (extra columns to
show, which must be among the step's `emits.reportable`). The chain-file format itself is
illustrative; `tools/validate_chain.py` takes the list of loaded step manifests.

Status legend: **exists today** means a `step.toml` and strategy are in this repo; **future**
means no strategy or manifest yet (hypothetical id).

## 1. Screen, filter, size, execute (mostly future)

Filter on ROE and EMA200, and show market cap and dividend yield even though they are not
filtered on.

```toml
[[steps]]
id = "screen.index_members"          # future: starting universe (consumes none, emits universe)
with = { index = "nifty200" }

[[steps]]
id = "filter.fundamental_trend"      # future
# LOOKS AT: roe (fundamental) and ema200 (indicator), via the filter's own params
with = { min_roe = 15.0, ema_period = 200 }
# REPORTS: not filtered on, only shown in the results
report = ["market_cap", "dividend_yield_pct"]

[[steps]]
id = "size.equal_weight"             # future here: a sizer, candidates -> weights (honba-examples has one)
with = { allocation = 0.95 }

[[steps]]
id = "execute.equal_weight"          # exists: portfolio/rebalancing/equal_weight/step.toml
# consumes weights (or a bare universe) and emits orders
```

The manifest behind `filter.fundamental_trend` would declare the looked-at and reported data
separately:

```toml
schema = 1
id = "filter.fundamental_trend"
kind = "filter"
title = "ROE and EMA trend filter"

[params.min_roe]
type = "float"
default = 15.0
min = 0.0
max = 100.0
step = 0.5
description = "Minimum ROE (%)."
sweepable = true

[params.ema_period]
type = "int"
default = 200
min = 20
max = 400
step = 1
description = "Keep symbols whose close is above this EMA."
sweepable = true

[requires]
bars = ["close"]
fundamentals = ["roe"]                               # looks at
indicators = [{ kind = "ema", period = "$ema_period", as = "trend" }]
history_bars = "$ema_period"

[consumes]
shape = "universe"
columns = ["symbol"]

[emits]
shape = "candidates"
adds = []
report = ["roe"]                                     # always shown
reportable = ["market_cap", "dividend_yield_pct"]    # shown only if the user asks

[chain]
after = ["screen"]
before = ["signal", "size"]
```

Compatibility: `screen` emits `universe`, `filter` consumes `universe` and emits `candidates`,
the sizer consumes `candidates` and emits `weights`, `execute.equal_weight` accepts `weights`
(its `consumes.shape` is the list `["weights", "universe"]`) and emits `orders`. Kinds run
screen, filter, size, execute, which is in order. The `report` list is accepted because both
columns are in `reportable`; asking for a column outside it is an error.

Exists today: the schema, `tools/validate_chain.py`, its rules and `execute.equal_weight`.
Future: the screen, filter and size ids above (no sizer is registered in this catalog; none of the
catalog strategies is a sizer).

## 2. Real registered ids (exists today)

Every registered step is self-contained: it takes a universe or symbol from its params and emits
orders (`side`, `quantity`). Today a chain is therefore a single trading step; screens, filters,
sizers and risk do not exist in this catalog yet.

```toml
[[steps]]
id = "signal.sma_crossover"          # exists: momentum/trend/sma_crossover/step.toml
with = { fast = 10, slow = 30, allocation = 0.5 }
```

Portfolio form (exists). The six portfolio strategies are `execute` steps: they consume a
`universe` and do selection, weighting and scheduling themselves.

```toml
[[steps]]
id = "execute.alpha30_momentum"      # exists: universe/alpha/momentum/step.toml
with = { select = "top:5:momentum:60", schedule = "monthly:first_session" }
```

Not valid (a signal already emits `orders`, and a sizer consumes `candidates`); the validator
reports it and explains that sizing belongs in a screen -> filter -> size -> execute chain:

```toml
[[steps]]
id = "signal.sma_crossover"

[[steps]]
id = "size.equal_weight"
```
