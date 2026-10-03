# alpha30_factor

Equal-weight portfolio of the **Nifty200 Alpha 30** index, rebalanced every 15 trading days.


## Behaviour

1. On start (and on every rebalance) the strategy obtains the current Alpha-30 membership.
2. Capital is split equally across the 30 names.
3. Every 15 trading days:
   - any stock that has left the index is sold completely,
   - any stock that has been added is bought to the target equal weight,
   - existing holdings are trimmed / topped-up so that each position is again equal-weight
     (sells the over-performers, buys the under-performers).

## Parameters

| key             | default   | meaning                              |
|-----------------|-----------|--------------------------------------|
| capital         | 1 000 000 | total INR allocated to the strategy  |
| allocation      | 0.98      | fraction of capital actually invested |
| rebalance_days  | 15        | trading days between rebalances      |
| seed_symbols    | []        | optional static list (fallback only) |

## Tags

`alpha_universe`, `equal_weight`, `rebalance`