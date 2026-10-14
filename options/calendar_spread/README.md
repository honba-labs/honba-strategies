# calendar_spread

Intended: trade a calendar spread across two option expiries (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Mid prices on both legs are optimistic; four-sided spreads are wide.
- The result depends on implied volatility term structure: use real historical IV, not a model.
- Early assignment, margin and expiry-day moves are hard to backtest.
