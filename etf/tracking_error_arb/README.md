# tracking_error_arb

Intended: trade the gap between an ETF price and its NAV or index (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- NAV is published after the session: using it intraday is lookahead.
- The gap is usually smaller than the spread, impact and costs; fills at the mid are unrealistic.
- Thin ETF liquidity limits size; backtested size will not be executable.
