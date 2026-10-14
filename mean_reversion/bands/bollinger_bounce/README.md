# bollinger_bounce

Intended: buy at the lower and sell at the upper Bollinger band (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Bands recompute each bar; entering on the close that breaches them needs a next-open fill.
- Strong trends keep walking the band and produce large losses; add a regime check.
- Period and width parameters overfit; validate out-of-sample.
