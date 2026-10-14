# international_diversification

Intended: spread allocation across domestic and international ETFs (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- Currency moves and the INR price of overseas ETFs can dominate the diversification effect.
- Overseas ETFs trade at premiums and have purchase limits; the backtest ignores both.
- Choosing the ETF set with hindsight (funds that survived and did well) is survivorship bias.
