# category_rotation

Intended: rotate between mutual fund categories (inferred from the name only; no design exists yet).

Status: scaffold — not implemented

## Usage

Not implemented.

## Possible output

No output yet.

## Pitfalls

Generic checks for this strategy type, to apply when it is implemented:

- NAV is declared after the close and orders cut off earlier: apply the NAV lag.
- Choosing categories and funds with hindsight is survivorship bias; closed or merged funds vanish.
- Exit loads, taxes and slow redemption are not in a bar-based backtest.
