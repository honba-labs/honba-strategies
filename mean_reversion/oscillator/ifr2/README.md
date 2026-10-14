# ifr2

Long-only RSI(2) dip buying above the Ichimoku cloud; exit when the close clears the highs of the two previous bars. The original's Hilbert trend-mode filter is dropped.

- **Category:** mean reversion / oscillator
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `oversold`, `tenkan`, `kijun`, `senkou_b`, `displacement`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest mean_reversion/oscillator/ifr2` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), then run it through the `honba.strategies.testing.replay` harness. This snippet is runnable from the repo root with `honba` installed:

```python
import math

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

catalog = find_catalog(".")  # run from the honba-strategies checkout, or pass its path
cs = load_catalog_strategy("ifr2", catalog)  # config.toml is read into cs.config
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

To change parameters, update `cs.config.params` (for example `cs.config.params.update(oversold=5)`) before `cs.instantiate()`.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `oversold` | `10` | 1 to 50 (step 1) | yes | Buy when RSI(2) is below this |
| `tenkan` | `9` | 2 to 100 (step 1) | yes | Ichimoku conversion line period |
| `kijun` | `26` | 2 to 200 (step 1) | yes | Ichimoku base line period |
| `senkou_b` | `52` | 2 to 400 (step 1) | yes | Ichimoku span B period |
| `displacement` | `26` | 1 to 100 (step 1) | yes | Cloud displacement (bars) |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.ifr2`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
uses = "signal.ifr2"
with = { oversold = 10, tenkan = 9, kijun = 26, senkou_b = 52, displacement = 26 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat, RSI(2) is below `oversold` and the close is above both Ichimoku cloud spans, and a `SELL` of the whole position when the close is above the highest high of the two previous bars. Long-only, one position at a time.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 16 fills
  BUY  1005 @ 944.79 (bar 150)
  SELL 1005 @ 961.09 (bar 157)
  BUY  790 @ 1201.49 (bar 177)
fill_delay=1: 16 fills
  BUY  1005 @ 948.69 (bar 151)
  SELL 1005 @ 957.91 (bar 158)
  BUY  790 @ 1207.11 (bar 178)
```

The first `BUY` waits for the cloud (roughly `senkou_b + displacement` bars); here it is on bar 150. The exit is quick: the demo's first trade closes seven bars later.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- No stop, and the cloud is only an entry filter: once in, the position is held until the close exceeds the previous two highs, even if price falls through the cloud. A dip that turns into a breakdown is held with no limit on the loss. Look at the worst trade and the drawdown.
- Deviation from the original: the Hilbert trend-mode filter of the source strategy is dropped (see above), so this is not a faithful copy and its published results cannot be applied to it.
- Parameter-sweep overfitting: five sweepable params (`oversold` and the four Ichimoku numbers). Ichimoku 9/26/52 is a charting convention; sweeping it together with an RSI(2) threshold gives a large search space on short trade counts.
- Lookahead / fill timing: every decision uses the current bar's close, and sizing uses that close too (`whole_shares(capital, allocation, bar.close)`). `replay(fill_delay=0)` then fills at that same close, which you cannot do live (the close is only known once the session is over). The realistic model is the next bar's open (`fill_delay=1`, and the engine's `NextOpenExecution`); in the snippet above it moves fills, e.g. the first BUY 944.79 becomes 948.69 and the first SELL 961.09 becomes 957.91. The quantity was sized at the old close, so a gap up can also overshoot `capital * allocation`. Buying the close of an oversold bar and selling a small bounce is the most fill-sensitive pattern in the catalog.
- Cost sensitivity: short holds and small average gains, so costs take a large share. Note also `rsi < oversold` here is strict while `rsi2_connors` uses `<=`, so the two are not interchangeable at the same threshold.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Sizing and risk: the position is `floor(capital * allocation / close)` with the fixed `capital` param. Profits and losses are not compounded back in, and the default 95% allocation to one instrument means any single trade can move the whole account.
