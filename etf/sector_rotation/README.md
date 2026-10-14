# sector_rotation

Intended: rotate into the strongest sector ETFs or indices (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Ranking on the close and trading the same close is lookahead.
- Sector indices are not tradable; the ETF or futures used has tracking error and costs.
- Lookback and top-N chosen on one history overfit; test walk-forward.
