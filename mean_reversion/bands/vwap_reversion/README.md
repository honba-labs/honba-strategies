# vwap_reversion

Intraday long-only mean reversion to the session VWAP for NSE, in IST. Buy when the close is
below the lower VWAP band before `entry_cutoff`; exit at VWAP or at `squareoff`. Nothing is
carried overnight.

- **Category:** mean reversion / bands
- **Indicators** (`[indicators.vwap]`): `vwap` (`band_mult`), reset on each IST session day
- **Params:** `capital`, `allocation`, `entry_cutoff`, `squareoff` (HH:MM IST)
- **Costs:** applied by the Honba backtest engine (intraday STT, GST, stamp duty), not the strategy
- **Bars:** intraday (e.g. 5-minute) bars with volume

Test: `pytest mean_reversion/bands/vwap_reversion` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), then run it through the `honba.strategies.testing.replay` harness. This snippet is runnable from the repo root with `honba` installed:

```python
import math
from datetime import datetime, timedelta, timezone

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

catalog = find_catalog(".")  # run from the honba-strategies checkout, or pass its path
cs = load_catalog_strategy("vwap_reversion", catalog)
iid = InstrumentId(cs.config.symbol, cs.config.exchange)

IST = timezone(timedelta(hours=5, minutes=30))
bars = []
for day in (2, 3, 4):  # three sessions, 5-minute bars 09:15-15:25 IST
    t0 = datetime(2025, 1, day, 9, 15, tzinfo=IST)
    for k in range(75):
        c = (
            100 + 1.5 * math.sin(k / 6) - (6 if 20 <= k < 26 else 0)
        )  # a sharp mid-morning dip
        ts = int((t0 + timedelta(minutes=5 * k)).timestamp() * 1e9)
        bars.append(Bar(iid, ts, c, c + 0.2, c - 0.2, c, 5_000.0))

result = replay(cs.instantiate(), bars)  # fills at the signal bar's close
print(len(result.fills), "fills")
for f in result.fills:
    t = datetime.fromtimestamp(f.ts / 1e9, IST)
    print(f"  {f.side.name:4} {f.quantity:g} @ {f.price:.2f} ({t:%d %b %H:%M} IST)")
```

This strategy needs **intraday bars with real volume** (the VWAP is volume weighted and resets every IST session day). `bar.ts` must be integer nanoseconds since the epoch. Change `band_mult` in `cs.config.indicators["vwap"]`, and `entry_cutoff` / `squareoff` (HH:MM IST) in `cs.config.params`. The snippet above builds three synthetic 5-minute sessions, so it does not use the daily-bar template of the other READMEs and has no `fill_delay` comparison.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `entry_cutoff` | `14:30` |  | no | No new entries at or after this IST time (HH:MM); must be before squareoff |
| `squareoff` | `15:15` |  | no | Flatten at or after this IST time (HH:MM), before the broker's ~15:20 MIS auto square-off |
| `band_mult` | `2.0` | 0.5 to 4.0 (step 0.1) | yes | VWAP band half-width in standard deviations |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.vwap_reversion`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
id = "signal.vwap_reversion"
with = { band_mult = 2.0, entry_cutoff = "14:30", squareoff = "15:15" }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat, before `entry_cutoff`, and the close is below the lower VWAP band; and a `SELL` of the whole position when the close is back at or above the VWAP, at or after `squareoff`, or on the first bar of a new IST session (a position left open by missing bars). Long-only, nothing is meant to be carried overnight.

Real output of the snippet above, run on the synthetic series it builds (three identical sessions: a gentle sine wave with a sharp dip, **not market data**, so it shows the mechanics only and says nothing about profitability). `replay` fills at the signal bar's close:

```text
6 fills
  BUY  10137 @ 93.71 (02 Jan 10:55 IST)
  SELL 10137 @ 99.13 (02 Jan 12:05 IST)
  BUY  10137 @ 93.71 (03 Jan 10:55 IST)
  SELL 10137 @ 99.13 (03 Jan 12:05 IST)
  BUY  10137 @ 93.71 (04 Jan 10:55 IST)
  SELL 10137 @ 99.13 (04 Jan 12:05 IST)
```

Each session shows the same pattern: a `BUY` at 10:55 IST during the artificial dip and a `SELL` at 12:05 IST when the close returns to VWAP. The trades repeat identically only because the three synthetic sessions are identical copies.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Intraday data only: on daily bars every bar is its own session, so the VWAP is just that bar's hlc3 and the strategy is meaningless. The default symbol `NIFTY50` is an index, whose 'volume' is not a traded volume; for a real test use a tradable name (or its future) with real volume.
- Band is ~0 at the open: the VWAP bands are valid from the first bar of the session, but with one or two bars the volume-weighted deviation is almost zero. A close even slightly below the bar's hlc3 breaks the 'lower band' and buys. A quick check shows a first-bar close of 99.2 against an hlc3 of 99.73 triggers a BUY at 09:15. The strategy has no minimum-bars-into-session guard, so the first minutes produce noise entries.
- No stop, falling knife: it buys when price is more than `band_mult` deviations below VWAP and exits only at VWAP, at `squareoff`, or the next session. On a trend-down day the position can lose all day. There is also no cap on re-entries: after an exit it can buy again the same session.
- Fill optimism and timestamps: the buy is filled at the close of the bar that broke the band, a price you only know once that bar has ended, and `replay` fills it at exactly that price. Real fills on a moving intraday market (spread, queue, impact) are worse, more so after a sharp move. Also check whether your bar timestamps mean bar start or bar end, because `entry_cutoff` / `squareoff` compare `bar.ts` as given.
- Parameter-sweep overfitting: `band_mult` (0.5 to 4.0) is the only sweepable param, but the times (`entry_cutoff`, `squareoff`) and the bar size are also free choices, and intraday results change a lot with bar size. Fit them on a different period than you test on.
- Costs and regime: this trades intraday, so the intraday STT, GST, stamp duty and slippage are paid every day it trades, on a small expected gain. Days of strong one-way trend (news, expiry, gaps) are where the edge disappears. The result depends on the volatility regime, so test across calm and stressed periods. Keep `squareoff` ahead of the broker's MIS auto square-off (about 15:20, per the `config.toml` comment) so the strategy flattens the position, not the broker.
