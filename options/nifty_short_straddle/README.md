# nifty_short_straddle

Intended: sell an at-the-money Nifty straddle (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Unlimited-risk structure: a backtest without gap days and margin calls understates drawdown.
- Use real option quotes and the strike traded at that time, not a smoothed model.
- Selling volatility looks safe until a large move; test stress periods separately.
