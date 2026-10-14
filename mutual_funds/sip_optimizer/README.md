# sip_optimizer

Intended: tune the timing or size of systematic investment plan instalments (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Optimising instalment dates on past data is overfitting.
- Comparing to lump sum needs the same cash flows: use money-weighted returns.
- Dividend/growth option, NAV lag and exit loads change the result.
