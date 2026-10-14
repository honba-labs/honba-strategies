# covered_call

Intended: hold the underlying and sell calls against it (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Backtest the call premium with real quotes: model prices overstate what you can sell.
- Capped upside and full downside; one large rally or fall dominates the result.
- Lot size, assignment, dividends and tax treatment change realised returns.
