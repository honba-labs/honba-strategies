# opening_range_breakout

Intended: trade a breakout of the first minutes' high or low (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Trading the breakout bar's close, not the next bar, is lookahead.
- Opening-range definition (minutes) and stop/target are easy to overfit.
- Intraday costs and slippage on breakouts can exceed the edge.
