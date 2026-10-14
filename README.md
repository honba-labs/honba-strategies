# honba-strategies

Community strategy catalog.

## Layout

Strategies are grouped by category, and by sub-category where a category is large
(`momentum/trend/sma_crossover`). Directory names carry no ordering. Each strategy has
`strategy.py`, `config.toml`, `README.md`, `tests/` and `backtest_result.json`.

`registry.json` indexes the catalog. Each entry has a `path` (`<category>/<name>`) and `tags`,
which are the indicator families the strategy uses, following TradingView's grouping
(`moving_average`, `trend`, `momentum`, `volatility`, `volume`, `support_resistance`, `breadth`,
`statistical`; the same families as `honba.strategies.indicators`). A strategy lives in one directory but can
carry several tags. Entries have exactly these keys: `name`, `category`, `path`, `description`, `tags`
(no `keywords`; put search terms in the description). The `name` is the key `load_named` resolves; a
strategy's runtime id (`name` in `config.toml` / the class) may differ, e.g. registry `equal_weight` runs as
`equal_weight_rebalance`.

Every directory with a real `strategy.py` must be in `registry.json`. Placeholders (docstring-only
`strategy.py`) are not registered and carry `status = "scaffold"` in their `config.toml`; remove that line
and register the strategy when implementing it. `test_registry.py` enforces both.

Every registered strategy also has a `step.toml` beside its `config.toml`: a declarative step manifest
(params with bounds, what the step looks at, what it consumes and emits) so strategies can be chained and
rendered by a GUI from data alone. See `schema/README.md` for the schema and chaining rules,
`tools/validate_chain.py` for the validator, and `docs/step-manifest-examples.md` for worked chains.
`test_step_manifests.py` keeps each manifest in step with its `config.toml` and code.

Run the tests with `pytest` (needs `honba` importable, e.g. `pip install -e ../honba/python`). 
In CI, `.github/workflows/ci.yml` checks out the `honba` core (pinned to `HONBA_REF: main` in the workflow) and builds it via `maturin develop`, ensuring all strategies test against a known honba version.
