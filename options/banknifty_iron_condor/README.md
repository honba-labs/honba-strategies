# banknifty_iron_condor

Intended: sell a defined-risk iron condor on BankNifty (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Option chain data must be point-in-time; stale or interpolated quotes mislead.
- Strike selection and exits chosen with hindsight overfit; test across regimes (gap days, event days).
- Margin, spreads and four-leg slippage are large; a rare tail move can erase months of premium.
