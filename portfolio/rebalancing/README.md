# Rebalancing

Strategies that hold a whole universe and periodically bring every position back to its
target weight: names that left the universe are sold, names that joined are bought, and the
rest are trimmed or topped up.

| Strategy | Universe | Weighting | Schedule |
| :--- | :--- | :--- | :--- |
| [`equal_weight`](equal_weight/README.md) | Nifty200 Alpha 30 (configurable) | equal | every 15 trading days |

Selection-based variants (top-N by momentum, low volatility, ...) use the same layer with a
`select` param; see the [portfolio README](../README.md).
