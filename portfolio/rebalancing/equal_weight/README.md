# equal_weight

Equal-weight portfolio of a named universe, rebalanced on a fixed cadence. By default the
universe is the **Nifty200 Alpha 30** and the cadence is every 15 trading days.

This is a thin binding of `honba.strategies.portfolio.PortfolioStrategy` (class
`EqualWeightRebalance`); it replaces the former `universe/alpha/equal_weight`
(`Alpha30EqualWeight`), which behaves identically on the same bars.

## Rules
- Target weight is `allocation / N` of portfolio value (cash plus marked positions) per member.
- On each rebalance, in order: **sell** names that left the universe, **trim** overweight
  names, then **buy** joiners and top up underweight names, all in whole shares.
- The universe is re-read from the engine at every rebalance.

## Parameters (`[params]`)
| Key | Default | Description |
|---|---|---|
| universe | `nifty200_alpha30` | Engine-known universe name, or a list of symbols |
| weighting | `equal` | `equal`, or `inverse_vol[:lookback]` |
| schedule | `every:15d` | `every:<N>d`, `monthly:first_session`, `drift:<x>`; join with `+` |
| allocation | 0.995 | Fraction of portfolio value to deploy; the rest is a cash buffer |
| point_in_time | false | Use historical membership snapshots (see below) |

Capital is whatever cash the run starts with; it is not a strategy param.

## Point-in-time membership
By default the engine's *current* constituents are used for the whole run, which is
survivorship-biased in a long backtest. Set `point_in_time = true` for bias-free backtests
once a history has been registered with `honba.markets.india.universes.register_universe_history`;
the engine raises `ValueError` if none is registered rather than guess. The engine currently
ships no Alpha 30 history, so it is off by default.

## Membership
`universe = "nifty200_alpha30"` is known natively to `resolve_universe`; an unknown name
raises `ValueError` (there is no seed fallback).

## Learning-path counterparts
- `honba-examples/universes/03_alpha30_constituents.py` - membership helper
- `honba-examples/strategies/06_alpha30_equal_weight_declarative.py` - runnable demo
