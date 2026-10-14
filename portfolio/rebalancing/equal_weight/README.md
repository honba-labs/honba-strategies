# equal_weight

Equal-weight portfolio of a named universe, rebalanced on a fixed cadence. By default the
universe is the **Nifty200 Alpha 30** and the cadence is every 15 trading days.

This is a thin binding of `honba.strategies.portfolio.PortfolioStrategy` (class
`EqualWeightRebalance`); it replaces the former `universe/alpha/equal_weight`
(`Alpha30EqualWeight`), which behaves identically on the same bars. The registry name is
`equal_weight`; its runtime id (`name` in `config.toml`) is `equal_weight_rebalance`.

- **Category:** portfolio / rebalancing (multi-instrument, long-only)
- **Timeframe:** daily bars; the rebalance cadence counts sessions
- **Sizing:** whole shares, `floor(portfolio_value * allocation / N / price)` per name
- **Costs:** applied by the Honba backtest engine, not the strategy

## Rules
- Target weight is `allocation / N` of portfolio value (cash plus marked positions) per member.
- On each rebalance, in order: **sell** names that left the universe, **trim** overweight
  names, then **buy** joiners and top up underweight names, all in whole shares.
- The universe is re-read from the engine at every rebalance.
- The first rebalance happens once every member has a price (or on the next session).

## Membership
`universe = "nifty200_alpha30"` is known natively to `resolve_universe`; an unknown name
raises `ValueError` (there is no seed fallback). By default it returns the engine's single
hard-coded list of 30 symbols, whatever the date. See *Pitfalls* before setting
`point_in_time = true`: the history the engine registers for this universe is a placeholder.

## Learning-path counterparts
- `honba-examples/universes/03_alpha30_constituents.py` - membership helper
- `honba-examples/strategies/06_alpha30_equal_weight_declarative.py` - runnable demo

Test: `pytest portfolio/rebalancing/equal_weight` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), bind a `LedgerContext` with the starting cash, then run it through the `honba.strategies.testing.replay` harness on a multi-instrument bar stream. This snippet is runnable from the repo root with `honba` installed; the bars are synthetic, one per name per session:

```python
import math

from honba.entities.bar import Bar
from honba.markets.india.universes import resolve_universe
from honba.strategies.context import LedgerContext
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

DAY_NS = 86_400_000_000_000

# Run from the honba-strategies checkout, or pass its path to find_catalog.
catalog = find_catalog(".")
cs = load_catalog_strategy(
    "equal_weight", catalog
)  # config.toml is read into cs.config
# cs.config.params.update(...)  # optional: override params before cs.instantiate()

members = resolve_universe(cs.config.params["universe"])  # today list: 30 names
n = len(members)


def close(k, d):
    """Synthetic close of name k on session d: a drift, a slow wave and a wobble."""
    drift = 0.0015 * ((k % 7) - 3) * d
    wave = 0.05 * math.sin(d / 9 + k) + 0.02 * math.sin(d / 2.3 + 3 * k)
    return (100.0 + 40.0 * k) * (1 + drift + wave)


# 120 sessions, one bar per name per session, in the same name order every day.
bars = []
for d in range(1, 121):
    for k, iid in enumerate(members):
        o = close(k, d - 1) * (1 + 0.01 * math.sin(7 * d + k))  # gaps off the close
        c = close(k, d)
        hi, lo = max(o, c) * 1.005, min(o, c) * 0.995
        bars.append(Bar(iid, d * DAY_NS, o, hi, lo, c, 1e6))

# replay() counts delay in bars, not sessions: 0 fills at the close of the bar that
# triggered the order; n (one bar per name) fills at that name's next-session open.
for delay in (0, n):
    strat = cs.instantiate()
    strat.bind(LedgerContext(cash=1_000_000.0))
    result = replay(strat, bars, fill_delay=delay)
    days = sorted({f.ts // DAY_NS for f in result.fills})
    names = {f.instrument_id.symbol for f in result.fills}
    print(f"fill_delay={delay}: {len(result.fills)} fills, {len(names)} names")
    print("  fill sessions:", days[:6])
    for f in result.fills[:3]:
        sym, session = f.instrument_id.symbol, f.ts // DAY_NS
        print(
            f"  {f.side.name:4} {f.quantity:g} {sym} @ {f.price:.2f} (session {session})"
        )
    held = [i for i, q in strat.ctx.positions().items() if q]
    print(f"  held at end: {len(held)} names")
```

Change parameters by updating `cs.config.params` before `cs.instantiate()`, for example `cs.config.params.update(schedule="every:10d")`. Unknown keys and malformed values raise `ValueError` naming the key. `replay` is a test harness with no costs; for realistic simulation use `honba.backtest`.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `universe` | `"nifty200_alpha30"` | - | no | Engine universe name, or a list of `SYMBOL` / `SYMBOL:EXCHANGE` |
| `weighting` | `"equal"` | pattern in `step.toml` | no | `equal`, `inverse_vol` or `inverse_vol:<lookback>` |
| `schedule` | `"every:15d"` | pattern in `step.toml` | yes | `every:<N>d`, `monthly:first_session`, `drift:<x>`; join with `+` |
| `select` | unset | pattern in `step.toml` | no | `top:<n>:<momentum|low_vol|mean_reversion>:<lookback>`; omitted keeps every member |
| `allocation` | `0.995` | 0.01 to 1.0 (step 0.01) | no | Fraction of portfolio value deployed (the rest is cash); must be in (0, 1] |
| `point_in_time` | unset (false) | - | no | Use historical membership snapshots (named universes only) |
| `history_len` | unset (auto) | 1 to 2000 (step 1) | no | Closes kept per instrument; default `max(64, longest lookback)` |

Capital is whatever cash the run starts with; it is not a strategy param.

**As a chain step.** `step.toml` registers it as `execute.equal_weight`, an `execute` step that consumes a `universe` (or the `weights` of a size step) and emits `orders`:

```toml
[[steps]]
id = "execute.equal_weight"
with = { schedule = "every:15d" }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders only on rebalance sessions. The first rebalance buys all 30 names (`BUY`, whole shares, about `allocation / 30` of cash each). Later ones `SELL` leavers and overweight names first, then `BUY` joiners and underweight names, so most sessions emit nothing. It is long-only and never shorts.

Real output of the snippet above, run on the synthetic bars it builds (a drift, a wave and a wobble per name, **not market data**, so it shows the mechanics only). `fill_delay=0` fills at the close of the bar that triggered the order; `fill_delay=30` fills at that name's next-session open:

```text
fill_delay=0: 218 fills, 30 names
  fill sessions: [1, 16, 31, 46, 61, 76]
  BUY  328 ABCAPITAL @ 100.95 (session 1)
  BUY  228 ADANIENSOL @ 145.04 (session 1)
  BUY  176 ADANIGREEN @ 187.99 (session 1)
  held at end: 30 names
fill_delay=30: 219 fills, 30 names
  fill sessions: [2, 17, 32, 47, 62, 77]
  BUY  328 ABCAPITAL @ 101.95 (session 2)
  BUY  228 ADANIENSOL @ 145.99 (session 2)
  BUY  176 ADANIGREEN @ 187.45 (session 2)
  held at end: 30 names
```

**Recorded backtest** (`backtest_result.json`, `status: completed`, committed in c7f1dfe): 2026-01-30 to 2026-05-06, 69 sessions, starting capital 1,000,000 INR, final value 998,333.08 INR. The file does not say which data, universe snapshot (the config sets no `point_in_time`, so the engine's current list) or cost model was used; fees were charged (616.45 INR).

| Metric | Value |
|---|---|
| Total return | -0.17 % |
| CAGR (extrapolated) | -0.63 % |
| Max drawdown | -0.37 % |
| Sharpe (annualised) | -3.11 |
| Turnover | 1.07 |
| Average cash | 13.8 % |
| Total fees | 616.45 INR |
| Fills | 111 |

Read these as a smoke test of the pipeline, not as performance: the window is three months long, and a strategy that returned about -0.2 % has nothing to say about long-run equal weighting.

## Pitfalls

The points below are about *this* strategy's logic and configuration. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Equal weight is a bet of its own: it holds 1/30 of each name regardless of size, which tilts toward the smaller, more volatile members versus the index's own weights, and each rebalance sells winners and buys losers (a mild contrarian tilt). Compare against the index or a buy-and-hold basket of the same names, not against zero.
- Survivorship and hindsight in the universe: `universe = "nifty200_alpha30"` resolves to one hard-coded list of 30 symbols (`NIFTY_200_ALPHA_30_SYMBOLS` in the engine), applied to **every** date, so the backtest holds today's members in the past. The index is built by NSE from trailing alpha, which means the 30 names were picked partly *because* they did well recently; running them over the period that made them eligible is lookahead (the selection rule is from NSE's methodology, not checked in this repo).
- `point_in_time = true` does not fix this yet: the only history the engine registers (`default_alpha30_history`) gives all 30 names an inclusion date of 2005-04-01 and no exit, so `resolve_universe("nifty200_alpha30", as_of=2010-01-04)` returns all 30 (checked), including names that were not yet listed then (for example PAYTM and NYKAA, listed in 2021). The flag only stops the engine from raising. Register a real history with `register_universe_history` before relying on it.
- Warm-up: the first rebalance waits until all 30 names have a price, but fires one session later regardless, so a missing or late-listed symbol means the first portfolio is built from fewer names.
- Lookahead and fill timing: the rebalance is decided on the first bar of a new session, from a price map that mixes that bar's close with the previous close of every other name, and whole-share quantities are sized from those prices. `replay(fill_delay=0)` then fills at the last close. Orders sized at one price and filled at another can overshoot cash or leave drift. Compare the `fill_delay=0` and `fill_delay=30` blocks in the output above: next-session-open fills differ from same-close fills. Use the engine's next-open execution, and run it with costs on.
- Costs, turnover and impact: `replay` has no costs, slippage or market impact. Each rebalance trades many names at once, including small trims, and several members are mid-cap or volatile, so quoted-close fills are optimistic. The recorded backtest above shows fees of about 0.06-0.09 % of traded notional (the cost model used is not recorded), which excludes slippage and impact; a high-turnover variant needs a much larger gross edge.
- Rebalance-date sensitivity: the cadence counts sessions from the first rebalance (the first bar with every member priced), not calendar dates. Moving the start date by a few days moves every later rebalance, and equal-weight rebalancing returns depend on that. Test several start offsets and also `monthly:first_session` before trusting one number.
- Concentration: with 30 names each position is about 3.3 %, and the list has clusters (three Adani group names, several PSU names such as BHEL, SAIL and NATIONALUM), so one group event moves a large share of the book. Selecting 10 or 15 names makes it 10 % or 6.7 % per name. Position sizes are in whole shares, so tiny residual weights remain.
- Tax: the backtest ignores tax. Frequent trimming and rebalancing realises short-term capital gains on equity held under a year in India (check the current rate), and securities transaction tax applies on every sell.
- The one recorded backtest covers only 69 sessions (2026-01-30 to 2026-05-06), a single short regime. CAGR and Sharpe are annualised extrapolations of that window, and the data, universe snapshot and cost model that produced it are not recorded in this repo. Do not treat it as evidence of an edge.
