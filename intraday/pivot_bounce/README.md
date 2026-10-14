# pivot_bounce

Intended: trade bounces off daily pivot levels (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Pivots must be computed from the previous session only; using the current day's high/low is lookahead.
- Levels shared by many traders get crowded; fills at the exact level are optimistic.
- Many trades per day make costs and slippage dominate.
