# rsi_divergence

Intended: trade divergences between price and RSI (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Pivot highs and lows are only known after later bars; flagging them at the pivot is lookahead.
- Divergence rules are subjective and overfit easily.
- Signals are rare, so the sample is small: avoid conclusions from a few trades.
