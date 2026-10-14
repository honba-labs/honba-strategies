# Step manifests

`step.schema.json` (JSON Schema, draft 2020-12) describes `step.toml`, a file beside each
strategy's `config.toml`. It is data only: a GUI algo-designer can render a step's form, list
what it reads and produces, and check that steps chain, without importing any Python. It is
separate from `honba.strategies.manifest.StrategyManifest`, which is the runtime manifest
(subscriptions, warm-up) used by the engine.

A step declares what it **looks at** (`requires`: the data it filters or decides on, such as ROE
or an EMA200) separately from what it **reports** (`emits.report` / `emits.reportable`: columns
shown in results, such as market cap or dividend yield, even though the step does not filter on
them).

## Fields

| Field | Meaning |
|---|---|
| `schema` | Always `1`. |
| `id` | `<kind>.<registry name>`, e.g. `signal.sma_crossover`. |
| `kind` | `screen`, `filter`, `signal`, `size`, `risk` or `execute`. |
| `title`, `description`, `tags` | Display text and free-form semantic tags (not the indicator-family tags of `registry.json`). |
| `[params.<name>]` | One table per parameter: `type` (`int`, `float`, `bool`, `str`, `enum`, `date`, `symbols`, `window`), `default`, `min`/`max`/`step` (numbers), `choices` (enum), `pattern` (str regex), `description`, `sweepable`. `optional = true` means no default and the param may be omitted. |
| `[requires]` | What it looks at: `bars` (OHLCV columns), `fundamentals`, `indicators` (`kind` from `honba.strategies.indicators.list_indicators()`, its args, optional `as` alias), `history_bars`, `pit` (needs point-in-time data). An indicator arg or `history_bars` may be `"$param"` to bind it to a step param. |
| `[consumes]` | What it needs from the previous step: `shape` (one shape, or a list of accepted shapes) and `columns`. |
| `[emits]` | `shape`; `adds` (columns appended), `report` (always reported), `reportable` (extra columns a user may ask it to report). |
| `[chain]` | `after` / `before`: palette hints (kinds or `universe`). The enforced rule is the kind order below. |

Shapes: `universe`, `candidates`, `weights`, `orders`, `none`.

## Stage semantics

A portfolio chain moves data through fixed stages:

```
universe --screen--> candidates --filter--> candidates --size--> weights --execute--> orders / result
```

| Kind | Consumes | Emits | Meaning |
|---|---|---|---|
| `screen` | `universe` or `none` | `candidates` | Pick instruments from a universe. |
| `filter` | `candidates` | `candidates` | Narrow or annotate the candidates. |
| `signal` | `universe` | `orders` | Per-symbol timing: a single-instrument bar strategy (e.g. `signal.sma_crossover`). Standalone. |
| `size` | `candidates` | `weights` | Turn candidates into target weights. It does not trade. |
| `risk` | `orders` | `orders` | Adjust orders. |
| `execute` | `weights` **or** `universe` | `orders` or `result` | Trade. Given `weights` it executes them; given a `universe` it is a self-contained portfolio strategy that selects, weights and schedules itself (the `portfolio/` and `universe/alpha/` strategies). |

`signal` and `size` are both optional, but they are two different kinds of chain: a portfolio chain
is `screen -> filter -> size -> execute`, and a bar-strategy chain is a lone `signal` (or a lone
self-contained `execute`). A `signal` cannot feed a `size`: it already emits orders, and a sizer
needs candidates. The validator says so when you try.

## Chaining rules

`tools/validate_chain.py::validate_chain(steps)` returns a list of error strings; empty means valid.

1. Shape: the previous step's `emits.shape` must be one of the next step's accepted
   `consumes.shape` values (a single string, or a list). The first step must accept `universe`
   (supplied by its params) or `none`.
2. Columns: every `consumes.columns` entry must be provided by an earlier step's `emits.adds` or
   `emits.report` (or a column the user asked it to report from `reportable`), or be listed in the
   step's own `requires.fundamentals` (fetchable). Every universe row has `symbol`.
3. Kind order: `screen -> filter -> signal -> size -> risk -> execute`, repeats allowed, never
   going backwards. `signal` and `size` are each optional (see Stage semantics).
4. Params: values given to a step (`with = {...}`) must match the declared type, `min`/`max`,
   `choices` and `pattern`.

`test_step_manifests.py` enforces that every strategy in `registry.json` has a valid `step.toml`
whose params match `config.toml` (and any `Parameter()` declarations) and whose indicators exist.
`tools/mini_schema.py` is a small dependency-free validator for the schema subset used here.
