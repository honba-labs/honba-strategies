# sma_crossover

Long-only SMA crossover for NSE cash equities. Buy when the fast SMA is above
the slow SMA while flat; exit fully when it drops below.

- **Category:** momentum / trend
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `fast`, `slow`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Inspired by:** the classic golden-cross idea; ported from a Jesse example

Test: `pytest momentum/trend/sma_crossover` (needs `honba` on the path).

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
    "sma_crossover", catalog
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

To change parameters, update `cs.config.params` (for example `cs.config.params.update(fast=10, slow=30)`) before calling `cs.instantiate()`. `fast` must be below `slow`, otherwise the constructor raises `ValueError`.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `fast` | `20` | 2 to 50 (step 1) | yes | Fast SMA period (bars); must be below slow |
| `slow` | `50` | 5 to 200 (step 1) | yes | Slow SMA period (bars) |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.sma_crossover`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
uses = "signal.sma_crossover"
with = { fast = 20, slow = 50 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat and the fast SMA is above the slow SMA, and a `SELL` of the whole position when the fast SMA falls below the slow SMA. It is long-only (no short leg) and holds at most one position. Nothing is emitted until `slow` bars have been seen.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 8 fills
  BUY  801 @ 1185.83 (bar 50)
  SELL 801 @ 1223.63 (bar 63)
  BUY  1003 @ 946.54 (bar 143)
fill_delay=1: 8 fills
  BUY  801 @ 1180.08 (bar 51)
  SELL 801 @ 1229.17 (bar 64)
  BUY  1003 @ 952.06 (bar 144)
```

With the shipped 20/50 periods the first order is a `BUY` on bar 50 (the first bar with a 50-bar SMA), and each buy is later closed by a single `SELL` of the same quantity.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Parameter-sweep overfitting: `fast` (2 to 50) and `slow` (5 to 200) are both sweepable, which is 8,523 valid `fast < slow` pairs on the full bounds. The best pair on one history is mostly noise-fitting. Prefer a flat plateau of good pairs over a single peak, and validate walk-forward / out-of-sample.
- Code vs config defaults: `strategy.py` declares `Parameter()` defaults of 10/30 while the shipped `config.toml` (and `step.toml`) use 20/50, and the constructor reads `config.toml`. Check which pair a result was produced with; `test_step_manifests.py` records the mismatch.
- Lookahead / fill timing: every decision uses the current bar's close, and sizing uses that close too (`whole_shares(capital, allocation, bar.close)`). `replay(fill_delay=0)` then fills at that same close, which you cannot do live (the close is only known once the session is over). The realistic model is the next bar's open (`fill_delay=1`, and the engine's `NextOpenExecution`); in the snippet above it moves fills, e.g. the first BUY 1185.83 becomes 1180.08 and the first SELL 1223.63 becomes 1229.17. The quantity was sized at the old close, so a gap up can also overshoot `capital * allocation`.
- Whipsaw and regime: a moving-average crossover loses repeatedly in sideways markets (buy after the rise, sell after the fall) and earns its keep in a few long trends. A backtest that happens to span one big trend overstates it, and the lag means exits come after a large part of the drop.
- Start-date dependence: entry is a *state* test, not a crossing event, so if the data starts in an up-state the first warmed-up bar buys straight away, in the middle of a move. Results can shift a lot with the first bar of your sample; test several start dates.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Costs and slippage: the STT, GST and stamp duty of the Honba backtest engine are charged per fill, so a round trip is charged on both its buy and its sell leg. A strategy that trades often needs a larger gross edge to survive them; run it through the engine with the cost pack on, not only through `replay` (which has no costs). Few trades per year keeps this mild, but it grows quickly as `fast` and `slow` shrink.
