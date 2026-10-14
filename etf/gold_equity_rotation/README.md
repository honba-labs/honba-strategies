# gold_equity_rotation

Intended: rotate between a gold ETF and an equity ETF (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Rotation signal lookahead: decide on the close, trade the next open.
- ETF tracking error, premium or discount to NAV, and the spread are missing from bar-close fills.
- Few regime switches mean a tiny sample: do not trust one favourable gold cycle.
