# alpha30_equal_weight

Equal-weight portfolio of the **Nifty200 Alpha 30**.

## Rules
- Capital is split equally across every stock currently in the index.
- Rebalance every 15 trading days.
- On rebalance day:
  - **Sell** any stock that left the index.
  - **Buy** any stock that joined the index.
  - For stocks that stayed: sell the overweight (relative winners) and buy the underweight (relative laggards) so each position returns to equal weight.

## Parameters
| Key             | Default | Description                       |
|-----------------|---------|-----------------------------------|
| capital         | 1e6     | Total capital (INR)               |
| allocation      | 0.98    | Fraction of capital to deploy     |
| rebalance_days  | 15      | Trading days between rebalances   |

## Membership
Always obtained via `resolve_universe("nifty200_alpha_30")`.  
A documented seed list is injected only when the engine does not yet know the name (CI / early learning environments).

## Learning-path counterparts
- `honba-examples/universes/03_alpha30_constituents.py` – membership helper
- `honba-examples/universes/04_universe_rebalance.py` – generic rebalancer
- `honba-examples/universes/06_alpha30_equal_weight_rebalance.py` – runnable demo