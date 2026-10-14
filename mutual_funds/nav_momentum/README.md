# nav_momentum

Intended: buy funds with strong recent NAV momentum (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- NAV is known after the close: trading on the same day's NAV is lookahead.
- Funds that closed or merged drop out of datasets: survivorship bias.
- Exit loads and tax on short holds can erase the momentum edge.
