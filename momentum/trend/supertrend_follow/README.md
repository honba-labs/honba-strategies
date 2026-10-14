# supertrend_follow

Long-only Supertrend trend follower for NSE cash equities. Buy while the Supertrend is
in an uptrend and flat; exit fully when it flips to a downtrend.

- **Category:** momentum / trend
- **Indicators** (`[indicators.trend]` in `config.toml`): `supertrend` (`atr_period`, `factor`), built through `IndicatorBank`
- **Params:** `capital`, `allocation` (whole-share sizing)
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy

Change the indicator's parameters in `config.toml` without touching code. The indicator itself must stay a `supertrend`: the strategy reads its `direction`.

Test: `pytest momentum/trend/supertrend_follow` (needs `honba` on the path).

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
    "supertrend_follow", catalog
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

To change parameters, update `cs.config.indicators["trend"]` (for example `cs.config.indicators["trend"]["factor"] = 2.0`) before `cs.instantiate()`; `capital` and `allocation` are in `cs.config.params`. The indicator parameters live in `[indicators.trend]`, not `[params]`; `step.toml` binds `atr_period` and `factor` to them.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `atr_period` | `10` | 2 to 100 (step 1) | yes | Supertrend ATR length |
| `factor` | `3.0` | 0.5 to 10.0 (step 0.5) | yes | Band width in ATRs |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.supertrend_follow`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
id = "signal.supertrend_follow"
with = { atr_period = 10, factor = 3.0 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat and the Supertrend direction is up, and a `SELL` of the whole position when the direction flips down. Long-only, one position at a time, silent while the indicator warms up.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 9 fills
  BUY  775 @ 1225.64 (bar 28)
  SELL 775 @ 1200.71 (bar 46)
  BUY  1169 @ 812.39 (bar 135)
fill_delay=1: 9 fills
  BUY  775 @ 1231.28 (bar 29)
  SELL 775 @ 1206.71 (bar 47)
  BUY  1169 @ 815.87 (bar 136)
```

Each `BUY` is followed by one `SELL` of the same quantity when the Supertrend flips; the flip level trails price, so the exit acts like a trailing stop that is only evaluated at the bar close.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Parameter-sweep overfitting: only two sweepable params (`atr_period` 2 to 100, `factor` 0.5 to 10, which is 1,980 combinations at the manifest steps). That is a small space, but a 10/3.0 default is a convention, not a fitted value; still validate any change walk-forward and prefer a plateau.
- The trend flip is the stop, but it is evaluated only on the close. A gap through the band exits at whatever price the next fill gets, and `replay(fill_delay=0)` exits at the same close, which is optimistic. With `fill_delay=1` (the engine's `NextOpenExecution` model) the snippet's first BUY moves from 1225.64 to 1231.28 and the first SELL from 1200.71 to 1206.71.
- Whipsaw: in a sideways market Supertrend flips often, and each flip round trip loses a little to the lag plus costs. Trend followers profit in a minority of periods; a backtest in one trending regime overstates what to expect.
- Start-date dependence: entry is a *state* test, not a crossing event, so if the data starts in an up-state the first warmed-up bar buys straight away, in the middle of a move. Results can shift a lot with the first bar of your sample; test several start dates.
- Config coupling: the strategy reads `trend.direction`, so `[indicators.trend]` must stay a `supertrend`. Swapping its `kind` for another indicator (such as `sma`) does not work: the strategy raises `AttributeError` on the first bar. The 'change the indicator' wording in older docs applies to the parameters only.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Costs and slippage: the STT, GST and stamp duty of the Honba backtest engine are charged per fill, so a round trip is charged on both its buy and its sell leg. A strategy that trades often needs a larger gross edge to survive them; run it through the engine with the cost pack on, not only through `replay` (which has no costs).
