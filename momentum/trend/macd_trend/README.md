# macd_trend

Long-only MACD trend follower. Buy when MACD is above its signal line and the close is above the trend EMA; exit fully when MACD is below signal and the close is below the EMA.

- **Category:** momentum / trend
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `ema`, `fastperiod`, `slowperiod`, `signal`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/trend/macd_trend` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), then run it through the `honba.strategies.testing.replay` harness. This snippet is runnable from the repo root with `honba` installed:

```python
import math

from honba.domain import Bar, InstrumentId
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

catalog = find_catalog(".")  # run from the honba-strategies checkout, or pass its path
cs = load_catalog_strategy("macd_trend", catalog)  # config.toml is read into cs.config
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

To change parameters, update `cs.config.params` (for example `cs.config.params.update(ema=150)`) before `cs.instantiate()`. `fastperiod` must be below `slowperiod`; `seed` (`"sma"` for TA-Lib style, `"first"` for Jesse style) chooses how the EMAs are initialised.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `ema` | `100` | 5 to 400 (step 1) | yes | Trend EMA period (bars) |
| `fastperiod` | `12` | 2 to 50 (step 1) | yes | MACD fast EMA period; must be below slowperiod |
| `slowperiod` | `26` | 5 to 100 (step 1) | yes | MACD slow EMA period |
| `signal` | `9` | 2 to 50 (step 1) | yes | MACD signal EMA period |
| `seed` | `sma` | sma, first | no | EMA seeding: "sma" (TA-Lib) or "first" (Jesse) |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.macd_trend`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
id = "signal.macd_trend"
with = { ema = 100, fastperiod = 12, slowperiod = 26, signal = 9 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat, MACD is above its signal line and the close is above the trend EMA, and a `SELL` of the whole position only when MACD is below its signal line **and** the close is below the EMA. Long-only, one position at a time; silent until the EMA and MACD have warmed up.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 10 fills
  BUY  1003 @ 946.54 (bar 143)
  SELL 1003 @ 937.28 (bar 153)
  BUY  939 @ 1011.32 (bar 160)
fill_delay=1: 10 fills
  BUY  1003 @ 952.06 (bar 144)
  SELL 1003 @ 938.95 (bar 154)
  BUY  939 @ 1017.31 (bar 161)
```

With the shipped `ema = 100` the first order cannot come before bar 100, and in this run it is a `BUY` on bar 143.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Parameter-sweep overfitting: four sweepable params (`ema` 5 to 400, `fastperiod` 2 to 50, `slowperiod` 5 to 100, `signal` 2 to 50). The product of those ranges is large, so some combination will always look good in-sample. Treat 12/26/9 as a convention rather than a fitted optimum, and validate any change walk-forward.
- Slow exit by design: the exit needs MACD below signal AND close below the EMA. That filters out noise but means a trend reversal is only acted on after a large part of the move has gone. Drawdown per trade can be big and is not capped by any stop.
- Lookahead / fill timing: every decision uses the current bar's close, and sizing uses that close too (`whole_shares(capital, allocation, bar.close)`). `replay(fill_delay=0)` then fills at that same close, which you cannot do live (the close is only known once the session is over). The realistic model is the next bar's open (`fill_delay=1`, and the engine's `NextOpenExecution`); in the snippet above it moves fills, e.g. the first BUY 946.54 becomes 952.06 and the first SELL 937.28 becomes 938.95. The quantity was sized at the old close, so a gap up can also overshoot `capital * allocation`.
- Indicator seeding and warmup: `seed` (`sma` vs `first`) changes the early EMA values, so results over the first few hundred bars differ between the two. The strategy needs `ema` bars before it can trade; do not read signals from the warmup region.
- Start-date dependence: entry is a *state* test, not a crossing event, so if the data starts in an up-state the first warmed-up bar buys straight away, in the middle of a move. Results can shift a lot with the first bar of your sample; test several start dates.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Costs and slippage: the STT, GST and stamp duty of the Honba backtest engine are charged per fill, so a round trip is charged on both its buy and its sell leg. A strategy that trades often needs a larger gross edge to survive them; run it through the engine with the cost pack on, not only through `replay` (which has no costs).
