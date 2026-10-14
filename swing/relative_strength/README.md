# relative_strength

Intended: buy stocks outperforming a benchmark or peers (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Ranking on the close and trading the same close is lookahead.
- Survivorship: use a point-in-time universe, not today's constituents.
- Lookback and top-N tuned on one history overfit; validate out-of-sample.
