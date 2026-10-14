# gap_fill

Intended: fade the opening gap back toward the prior close (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Opening-gap fills assume you trade the auction price; real fills slip, especially on big gaps.
- Gaps on news (results, corporate actions) often do not fill; adjust bars for splits and filter events.
- Costs per round trip are large against small intraday moves.
