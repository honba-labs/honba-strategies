# sector_leadership

Intended: buy stocks in the leading sectors (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Sector membership changes over time: use point-in-time classifications.
- Leader ranking on the close with a same-close fill is lookahead.
- Sector leadership flips fast; a short sample can look better than it is.
