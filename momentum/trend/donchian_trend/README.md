# donchian_trend

Long-only Donchian breakout. Buy a close above the previous N-bar high while above the trend SMA; exit fully on a close below the previous N-bar low.

- **Category:** momentum / trend
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `period`, `trend_sma`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/trend/donchian_trend` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), then run it through the `honba.strategies.testing.replay` harness. This snippet is runnable from the repo root with `honba` installed:

```python
import math

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

catalog = find_catalog(".")  # run from the honba-strategies checkout, or pass its path
cs = load_catalog_strategy(
    "donchian_trend", catalog
)  # config.toml is read into cs.config
# cs.config.params.update(...)  # optional: override params before cs.instantiate()

iid = InstrumentId(cs.config.symbol, cs.config.exchange)


def px(i):  # synthetic series: a slow wave, a fast wave and a drift
    return 1000 + 250 * math.sin(i / 25) + 60 * math.sin(i / 4.3) + i * 0.2


bars = []
for i in range(600):
    o = px(i - 1) + 6 * math.sin(7 * i)  # opens gap a little from the prior close
    c = px(i)
    bars.append(Bar(iid, i + 1, o, 1.01 * max(o, c), 0.99 * min(o, c), c, 1e6))

for delay in (0, 1):  # 0: fill at the signal bar's close; 1: at the next bar's open
    result = replay(cs.instantiate(), bars, fill_delay=delay)
    print(f"fill_delay={delay}: {len(result.fills)} fills")
    for f in result.fills[:3]:
        print(f"  {f.side.name:4} {f.quantity:g} @ {f.price:.2f} (bar {f.ts})")
```

To change parameters, update `cs.config.params` (for example `cs.config.params.update(period=55)`) before `cs.instantiate()`.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `period` | `20` | 2 to 200 (step 1) | yes | Channel lookback (bars, excludes the current bar) |
| `trend_sma` | `200` | 2 to 400 (step 1) | yes | Trend filter SMA period |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.donchian_trend`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
id = "signal.donchian_trend"
with = { period = 20, trend_sma = 200 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat, the close is above the trend SMA and above the highest high of the previous `period` bars, and a `SELL` of the whole position when the close drops below the lowest low of the previous `period` bars. Long-only, one position at a time.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 4 fills
  BUY  952 @ 997.49 (bar 303)
  SELL 952 @ 1241.06 (bar 369)
  BUY  915 @ 1037.34 (bar 463)
fill_delay=1: 4 fills
  BUY  952 @ 995.01 (bar 304)
  SELL 952 @ 1244.50 (bar 370)
  BUY  915 @ 1031.93 (bar 464)
```

The 200-bar trend SMA means nothing can happen before bar 200; here the first `BUY` is on bar 303 and only 4 fills happen in 600 bars, which is typical for a slow breakout system.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Parameter-sweep overfitting: `period` (2 to 200) and `trend_sma` (2 to 400) give 79,401 combinations on the full bounds. Few trades per year means few independent samples to fit on, so a tuned pair is fragile. Prefer round, well-known values (20/55 day channels, 200 day SMA) and check neighbouring values behave similarly.
- Lookahead: the channel is built from the *previous* bars (the breakout level never includes the current bar), so there is no lookahead inside the indicator. The signal is still taken on the close of the breakout bar, and `replay(fill_delay=0)` fills at that same close, which you cannot do live. With `fill_delay=1` (the engine's `NextOpenExecution` model) the snippet's first BUY moves from 997.49 to 995.01 and the first SELL from 1241.06 to 1244.50. Sizing uses the signal bar's close, so a gap can overshoot `capital * allocation`.
- Small samples: in the synthetic run 600 bars produced only 4 fills. On real data a handful of big trends will dominate the result; confidence intervals are wide. Do not read a high backtested CAGR as skill without enough independent trades.
- Breakouts fail often: the strategy pays the false breakout loss many times for each trend it catches, and the exit (a close below the N-bar low) comes after a drop. It has no separate stop, so the exit channel is the only protection.
- Start-date dependence: entry is a *state* test, not a crossing event, so if the data starts in an up-state the first warmed-up bar buys straight away, in the middle of a move. Results can shift a lot with the first bar of your sample; test several start dates.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Sizing and risk: the position is `floor(capital * allocation / close)` with the fixed `capital` param. Profits and losses are not compounded back in, and the default 95% allocation to one instrument means any single trade can move the whole account.
