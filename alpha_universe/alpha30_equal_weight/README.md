# alpha30_equal_weight

Equal-weight portfolio of the **Nifty200 Alpha 30**, rebalanced every 15 trading days.

## Behaviour

1. Obtain the current Alpha-30 membership (live universe from the engine, or `seed_symbols`).
2. Split `capital * allocation` equally across the N names.
3. Every `rebalance_days` trading days:
   - **sell** any holding that left the index,
   - **buy** any name that entered,
   - **trim / top-up** remaining names so each is again equal-weight
     (sells over-performers, buys under-performers).

## Params (`config.toml`)

| key | default | meaning |
|-----|---------|---------|
| `capital` | 1_000_000 | INR allocated to the strategy |
| `allocation` | 0.98 | fraction of capital invested |
| `rebalance_days` | 15 | trading days between rebalances |
| `universe` | `NIFTY200_ALPHA_30` | engine universe key |
| `seed_symbols` | [] | offline fallback membership |

## Notes

- Long-only NSE cash equities; no short leg.
- Sizing uses `whole_shares` (lot-aware floor).
- Costs (STT, GST, stamp duty) and slippage are applied by the Honba engine.
- Category: `alpha_universe`
- Tags: `alpha_universe`, `breadth`, `statistical`

Test: `pytest alpha_universe/alpha30_equal_weight` (needs `honba` on the path).