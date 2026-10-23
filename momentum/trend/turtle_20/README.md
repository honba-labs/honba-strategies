# turtle_20

Simplified Turtle System 1, long-only, no pyramiding. Buy a break of the previous `entry`-bar high; exit on a close below the previous `exit`-bar low or a 2 x ATR protective stop.

- **Category:** momentum / trend
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `entry`, `exit`, `atr_period`, `atr_mult`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest momentum/trend/turtle_20` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), then run it through the `honba.strategies.testing.replay` harness. This snippet is runnable from the repo root with `honba` installed:

```python
import math

from honba.domain import Bar, InstrumentId
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

catalog = find_catalog(".")  # run from the honba-strategies checkout, or pass its path
cs = load_catalog_strategy("turtle_20", catalog)  # config.toml is read into cs.config
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

To change parameters, update `cs.config.params` (for example `cs.config.params.update(entry=55, exit=20)`) before `cs.instantiate()`. `atr_first_bar = true` reproduces Jesse's first true range (high minus low).

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `entry` | `20` | 2 to 200 (step 1) | yes | Entry breakout lookback (bars) |
| `exit` | `10` | 2 to 100 (step 1) | yes | Exit channel lookback (bars) |
| `atr_period` | `20` | 2 to 100 (step 1) | yes | ATR period for the protective stop |
| `atr_mult` | `2.0` | 0.5 to 10.0 (step 0.25) | yes | Stop distance in ATRs below entry |
| `atr_first_bar` | `False` |  | no | True: the first true range is high-low (Jesse's convention) |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.turtle_20`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
id = "signal.turtle_20"
with = { entry = 20, exit = 10, atr_period = 20, atr_mult = 2.0 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat and the close breaks above the highest high of the previous `entry` bars (once the ATR is ready), and a `SELL` of the whole position when the close falls below the previous `exit`-bar low, or when the bar's low touches the protective stop (`fill price - atr_mult * ATR` taken at the fill). No pyramiding.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 9 fills
  BUY  811 @ 1170.86 (bar 25)
  SELL 811 @ 1251.01 (bar 42)
  BUY  1113 @ 853.13 (bar 137)
fill_delay=1: 8 fills
  BUY  811 @ 1166.06 (bar 26)
  SELL 811 @ 1245.21 (bar 43)
  BUY  1113 @ 848.77 (bar 138)
```

Note the fill counts differ between `fill_delay=0` (9 fills) and `fill_delay=1` (8 fills) in this run: moving the fill by one bar shifts the stop level and the exit bars, so the trade path itself can change, not just the prices (the 9-fill run ends still holding a position, the 8-fill run ends flat).

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Parameter-sweep overfitting: four sweepable params (`entry` 2 to 200, `exit` 2 to 100, `atr_period` 2 to 100, `atr_mult` 0.5 to 10). The famous 20/10 and 55/20 pairs are conventions; a sweep that finds 37/13 on your sample is fitting noise. Validate walk-forward.
- The protective stop is not a resting order. The strategy checks `bar.low <= stop` after the bar is complete and then sells at the close (or at the next open with `fill_delay=1`). The real exit price is usually worse than the stop, much worse on a gap, so realised losses can exceed `atr_mult * ATR`.
- Lookahead / fill timing: every decision uses the current bar's close, and sizing uses that close too (`whole_shares(capital, allocation, bar.close)`). `replay(fill_delay=0)` then fills at that same close, which you cannot do live (the close is only known once the session is over). The realistic model is the next bar's open (`fill_delay=1`, and the engine's `NextOpenExecution`); in the snippet above it moves fills, e.g. the first BUY 1170.86 becomes 1166.06 and the first SELL 1251.01 becomes 1245.21. The quantity was sized at the old close, so a gap up can also overshoot `capital * allocation`. The stop level itself is computed from the fill price and the ATR at fill time, so it also moves with the fill model.
- Simplified Turtle: the original sizes positions by volatility (ATR risk units), pyramids up to four units and skips a signal after a winning trade. None of that is implemented here; a fixed 95% allocation with a 2 ATR stop puts `0.95 * 2 * ATR / price` of the account at risk per trade, which is large on volatile names. Do not compare results with published Turtle performance.
- Path dependence: the entry is a fresh breakout of the previous N-bar high, but whether you are already in a trade (and where its stop sits) depends on the earlier path. A different first bar changes which breakouts are taken, so test several start dates.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Costs and slippage: the STT, GST and stamp duty of the Honba backtest engine are charged per fill, so a round trip is charged on both its buy and its sell leg. A strategy that trades often needs a larger gross edge to survive them; run it through the engine with the cost pack on, not only through `replay` (which has no costs).
