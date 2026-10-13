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

Run the tests with `pytest` (needs `honba` importable, e.g. `pip install -e ../honba/python`).
