# expiry_day_scalp

Intended: scalp options on expiry day (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Expiry-day premiums move fast and spreads widen: bar-close fills are unrealistic.
- Gamma risk and settlement rules mean tiny sample sizes hide tail losses.
- Cost per trade is large against small premium moves.
