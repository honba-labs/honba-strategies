# breakout_52week

Intended: buy a break above the 52-week high (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- The 52-week high must exclude the current bar, or the breakout is always true.
- Survivorship: use a point-in-time universe, not today's constituents.
- Breakouts fail often; false-break whipsaws and gap-up fills hurt returns.
