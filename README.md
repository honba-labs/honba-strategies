# honba-strategies

Community strategy catalog.

## Layout

Strategies are grouped by category, and by sub-category where a category is large
(`momentum/trend/sma_crossover`). Directory names carry no ordering. Each strategy has
`strategy.py`, `config.toml`, `README.md`, `tests/` and `backtest_result.json`.

`registry.json` indexes the catalog. Each entry has a `path` (`<category>/<name>`) and `tags`,
which are the indicator families the strategy uses (`trend`, `momentum`, `volatility`, `volume`,
the same families as `honba.strategies.indicators`). A strategy lives in one directory but can
carry several tags.

Run the tests with `pytest` (needs `honba` importable, e.g. `pip install -e ../honba/python`).
