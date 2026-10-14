# vwap_scalp

Intended: scalp moves around the session VWAP (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- VWAP built from the full day (not cumulative to the bar) is lookahead.
- Scalps need tight spreads; the backtest fill at the close or mid is unrealistic.
- Per-trade costs often exceed the small expected move; test net of costs.
