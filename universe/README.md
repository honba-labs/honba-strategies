# Alpha Universe

Strategies that trade the **Nifty200 Alpha 30** (and related alpha-tilted universes).

The Nifty200 Alpha 30 is an NSE strategy index of 30 stocks selected from the Nifty 200 on the basis of **Jensen’s Alpha**. Weights are driven by alpha scores (capped), and the index is reconstituted quarterly. All constituents are F&O-eligible, which keeps the universe liquid and practical for systematic execution.

This category groups portfolio-level strategies that:

- take the Alpha-30 membership (or a closely related alpha universe) as their tradable set,
- allocate capital across multiple names rather than a single symbol,
- rebalance on a fixed calendar or when membership changes.

## Strategies

| Strategy | Path | Idea |
|----------|------|------|
| **alpha30_momentum** | `universe/alpha/momentum` | Cross-sectional momentum tilt inside the Alpha-30 |
| **alpha30_low_vol** | `universe/alpha/low_vol` | Prefer lower-volatility names within the universe |
| **alpha30_quality** | `universe/alpha/quality` | Quality-factor ranking of Alpha-30 constituents |
| **alpha30_mean_reversion** | `universe/alpha/mean_reversion` | Short-horizon mean-reversion signals on the same set |
| **alpha30_factor** | `universe/alpha/factor` | Multi-factor combination (momentum + quality + low-vol) |

Each strategy directory contains the standard catalog files:

- `strategy.py` — Honba `Strategy` implementation
- `config.toml` — parameters (capital, rebalance frequency, etc.)
- `README.md` — strategy-specific notes
- `tests/` — unit / smoke tests
- `backtest_result.json` — reference back-test summary

## Common design patterns

- **Universe source** — prefer the engine’s live universe (`ctx.universe("NIFTY200_ALPHA_30")`). A static seed list in `config.toml` is only a fallback for offline tests.
- **Equal-weight or score-weight** — most strategies either equal-weight the current members or weight by a factor score, then rebalance periodically.
- **Membership changes** — on every rebalance, names that left the index are fully exited; names that entered are sized to target.
- **Rebalance cadence** — typically 15 trading days or quarterly (aligned with the official index review). Override via `rebalance_days` in `config.toml`.
- **Sizing** — use `honba.strategies.sizing.whole_shares` so lot-size constraints are respected; leave a small cash buffer (`allocation < 1.0`).

## Tags

Strategies in this folder commonly carry the tags:

- `alpha_universe`
- `breadth` / `statistical` (when ranking is used)
- `momentum`, `volatility`, or `trend` depending on the factor

## Running

```bash
# from the honba-strategies root (honba must be importable)
pytest alpha_universe/