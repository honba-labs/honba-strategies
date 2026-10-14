# bollinger_breakout

Long-only Bollinger breakout. Buy a close above the upper band (hl2 source) while above the Ichimoku cloud; exit fully on a close below the middle band.

- **Category:** momentum / breakout
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `period`, `mult`, `tenkan`, `kijun`, `senkou_b`, `displacement`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/breakout/bollinger_breakout` (needs `honba` on the path).

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
    "bollinger_breakout", catalog
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

To change parameters, update `cs.config.params` (for example `cs.config.params.update(mult=2.5)`) before `cs.instantiate()`.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `period` | `20` | 2 to 200 (step 1) | yes | Bollinger period (on hl2) |
| `mult` | `2.0` | 0.5 to 5.0 (step 0.1) | yes | Band width in standard deviations |
| `tenkan` | `9` | 2 to 100 (step 1) | yes | Ichimoku conversion line period |
| `kijun` | `26` | 2 to 200 (step 1) | yes | Ichimoku base line period |
| `senkou_b` | `52` | 2 to 400 (step 1) | yes | Ichimoku span B period |
| `displacement` | `26` | 1 to 100 (step 1) | yes | Cloud displacement (bars) |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.bollinger_breakout`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
id = "signal.bollinger_breakout"
with = { period = 20, mult = 2.0, tenkan = 9, kijun = 26, senkou_b = 52, displacement = 26 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat and the close is above both Ichimoku cloud spans and above the upper Bollinger band (bands are computed on the bar's (high + low) / 2), and a `SELL` of the whole position when the close falls below the middle band. Long-only, one position at a time.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 10 fills
  BUY  957 @ 991.83 (bar 159)
  SELL 957 @ 1276.69 (bar 204)
  BUY  952 @ 997.49 (bar 303)
fill_delay=1: 10 fills
  BUY  957 @ 996.44 (bar 160)
  SELL 957 @ 1282.62 (bar 205)
  BUY  952 @ 995.01 (bar 304)
```

The cloud needs roughly `senkou_b + displacement` bars of history; in this run the first `BUY` is on bar 159.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Parameter-sweep overfitting: six sweepable params (`period`, `mult`, `tenkan`, `kijun`, `senkou_b`, `displacement`), the most of any single-instrument trend strategy here. The Ichimoku 9/26/52 numbers are a charting convention, not something fitted to NSE; sweeping all six on one history will find a flattering but meaningless set. Keep conventions unless an out-of-sample test says otherwise.
- Cloud displacement is handled without lookahead (the spans used at bar t were computed `displacement` bars earlier), and the bands use the current bar's own (high + low) / 2. But the entry still compares the close with them and fills at that same close under `fill_delay=0`. In the snippet above a one-bar delay moves the first BUY from 991.83 to 996.44 and the first SELL from 1276.69 to 1282.62.
- Mixed price sources: the bands are built from hl2 while the breakout test uses the close, so the comparison is not the textbook close-vs-band one. Do not compare with other Bollinger implementations without checking the source price.
- Exit can be quick: the exit is the middle band (the 20-bar mean of hl2), which can be only a modest distance below an upper-band entry, so volatile bars give round trips that lose on costs alone.
- Long warmup and regime dependence: the cloud filter delays the first trade by roughly 78 bars with the defaults, and the whole entry only fires in persistent uptrends. In ranging markets it mostly stays out, and in choppy uptrends it buys the top of every spike.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Costs and slippage: the STT, GST and stamp duty of the Honba backtest engine are charged per fill, so a round trip is charged on both its buy and its sell leg. A strategy that trades often needs a larger gross edge to survive them; run it through the engine with the cost pack on, not only through `replay` (which has no costs).
