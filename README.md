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

## README and pitfalls conventions

Every strategy README follows the same shape, and `test_readme_sections.py` enforces it:

- **Registered strategies** (every entry in `registry.json`) must have `## Usage`, `## Possible output`
  and `## Pitfalls` sections (each at least 3 non-blank lines). `## Pitfalls` needs at least 3 bullets
  and must link the
  [avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html)
  page. Pitfalls should be specific to that strategy's code and config (survivorship in its universe,
  lookahead in its fill timing, overfitting in its sweepable params, costs, ...), not generic filler.
- **Usage** holds a snippet that runs from the repo root with `honba` installed (load by registry name with
  `honba.strategies.loader`, run through `honba.strategies.testing.replay`). **Possible output** shows the
  real output of that snippet, and quotes `backtest_result.json` metrics only when its `status` is
  `completed` (say where they came from). Run the snippet and paste what it prints.
- **Scaffolds** (`status = "scaffold"` in `config.toml`) are not registered. Their README must say
  `Status: scaffold`, keep the same three headings (one honest line under Usage and Possible output,
  3 generic pitfall bullets) and need no snippet. When you implement one, replace the stub with a full README.
- **`pitfalls` in `step.toml`**: each registered `step.toml` carries `pitfalls = [...]`, 2 to 4 one-line
  strings of 10 to 160 characters that a GUI can show when the step is added to a chain. They are the short
  form of the README's Pitfalls and are checked by the same test. Example:

  ```toml
  pitfalls = [
    "Tuned fast/slow pairs overfit; validate walk-forward or out-of-sample.",
    "Decides on the bar close; fill at the next open, not the same close.",
    "Whipsaws in sideways markets; lags trend turns.",
  ]
  ```

  The field is described in `schema/README.md`.

Run the tests with `pytest` (needs `honba` importable, e.g. `pip install -e ../honba/python`). 
In CI, `.github/workflows/ci.yml` checks out the `honba` core (pinned to `HONBA_REF: main` in the workflow) and builds it via `maturin develop`, ensuring all strategies test against a known honba version.
