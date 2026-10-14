# kdj_cross

Long-only KDJ momentum. Buy when J is above both K and D; exit when in profit and J turns down, when J drops below K or D, or on a 2 x ATR protective stop. Jesse's `J > (K and D)` only compared J with D; the intended J > K and J > D is used here.

- **Category:** momentum / oscillator
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `fastk`, `slowk`, `slowd`, `atr_period`, `atr_mult`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/oscillator/kdj_cross` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), then run it through the `honba.strategies.testing.replay` harness. This snippet is runnable from the repo root with `honba` installed:

```python
import math

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

catalog = find_catalog(".")  # run from the honba-strategies checkout, or pass its path
cs = load_catalog_strategy("kdj_cross", catalog)  # config.toml is read into cs.config
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

To change parameters, update `cs.config.params` (for example `cs.config.params.update(atr_mult=3.0)`) before `cs.instantiate()`. `slowk_ma` / `slowd_ma` pick the smoothing (`sma`, `ema`, `rma`, `wma`).

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `fastk` | `9` | 2 to 100 (step 1) | yes | Stochastic lookback (bars) |
| `slowk` | `3` | 1 to 20 (step 1) | yes | K smoothing |
| `slowd` | `3` | 1 to 20 (step 1) | yes | D smoothing |
| `atr_period` | `14` | 2 to 100 (step 1) | yes | ATR period for the protective stop |
| `atr_mult` | `2.0` | 0.5 to 10.0 (step 0.25) | yes | Stop distance in ATRs below entry |
| `atr_first_bar` | `False` |  | no | True: the first true range is high-low (Jesse's convention) |
| `slowk_ma` | `sma` | sma, ema, rma, wma | no | KDJ K smoothing moving average |
| `slowd_ma` | `sma` | sma, ema, rma, wma | no | KDJ D smoothing moving average |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.kdj_cross`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
uses = "signal.kdj_cross"
with = { fastk = 9, slowk = 3, slowd = 3, atr_period = 14, atr_mult = 2.0 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat and J is above both K and D (once the ATR is ready), and a `SELL` of the whole position when the close is above the entry price and J has turned down, or J drops below K or D, or the bar's low touches the stop at `fill price - atr_mult * ATR`. Long-only, one position at a time.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 138 fills
  BUY  845 @ 1123.45 (bar 21)
  SELL 845 @ 1170.86 (bar 25)
  BUY  799 @ 1188.24 (bar 26)
fill_delay=1: 137 fills
  BUY  845 @ 1127.11 (bar 22)
  SELL 845 @ 1166.06 (bar 26)
  BUY  799 @ 1186.97 (bar 27)
```

This is by far the most active strategy of the chunk: 138 fills in 600 bars (about 69 round trips), with entries and exits only a few bars apart. That frequency is the main risk to read from this sample.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Overtrading and cost sensitivity: J is the most volatile of the three KDJ lines, and the exit fires the moment J dips below K or D. In the synthetic run that is 138 fills in 600 bars. Per-trade costs (STT, GST, stamp duty, slippage) will eat a thin edge; always backtest through the engine with costs on and look at net, not gross, results.
- Parameter-sweep overfitting: five sweepable params (`fastk`, `slowk`, `slowd`, `atr_period`, `atr_mult`) plus the non-sweepable `slowk_ma` / `slowd_ma` choices. With this many trades, in-sample curves look smooth and convincing, which makes overfitting harder to notice. Validate walk-forward.
- Lookahead / fill timing: every decision uses the current bar's close, and sizing uses that close too (`whole_shares(capital, allocation, bar.close)`). `replay(fill_delay=0)` then fills at that same close, which you cannot do live (the close is only known once the session is over). The realistic model is the next bar's open (`fill_delay=1`, and the engine's `NextOpenExecution`); in the snippet above it moves fills, e.g. the first BUY 1123.45 becomes 1127.11 and the first SELL 1170.86 becomes 1166.06. The quantity was sized at the old close, so a gap up can also overshoot `capital * allocation`. With a trade every few bars, each fill-timing error is paid many times.
- The ATR stop is checked after the bar (`bar.low <= stop`) and sold at the close or next open, not at the stop price, so gap losses exceed `atr_mult * ATR`. In practice the J-based exits trigger long before the stop does.
- Porting note: Jesse's original compared J only with D; this version requires J > K and J > D (as the README notes). Results will not match the Jesse original, and the entry is a state test, so the first warmed-up bar can buy in the middle of a move.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Sizing and risk: the position is `floor(capital * allocation / close)` with the fixed `capital` param. Profits and losses are not compounded back in, and the default 95% allocation to one instrument means any single trade can move the whole account.
