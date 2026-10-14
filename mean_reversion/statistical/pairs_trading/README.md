# pairs_trading

Intended: trade the spread between two related stocks (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Choosing the pair with hindsight (cointegrated over the test window) is overfitting.
- Hedge ratio fitted on the whole sample is lookahead; estimate it on past data only.
- Short legs need futures or securities lending; overnight short selling of cash equities is restricted in India.
