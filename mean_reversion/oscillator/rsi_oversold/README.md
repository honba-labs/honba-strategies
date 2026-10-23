# rsi_oversold

Long-only daily mean reversion. Buy an oversold dip (RSI below `entry`) while the close is above the trend SMA; exit when RSI recovers above `exit` or after `max_hold` bars.

- **Category:** mean reversion / oscillator
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `rsi_period`, `entry`, `exit`, `trend_sma`, `max_hold`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest mean_reversion/oscillator/rsi_oversold` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), then run it through the `honba.strategies.testing.replay` harness. This snippet is runnable from the repo root with `honba` installed:

```python
import math

from honba.domain import Bar, InstrumentId
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

catalog = find_catalog(".")  # run from the honba-strategies checkout, or pass its path
cs = load_catalog_strategy(
    "rsi_oversold", catalog
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

To change parameters, update `cs.config.params` (for example `cs.config.params.update(trend_sma=0)`; `trend_sma = 0` disables the trend filter) before `cs.instantiate()`. The constructor requires `0 < entry < exit < 100`.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `rsi_period` | `4` | 2 to 50 (step 1) | yes | RSI period |
| `entry` | `25` | 1 to 50 (step 1) | yes | Buy when RSI is below this; must be below exit |
| `exit` | `60` | 30 to 99 (step 1) | yes | Sell when RSI is above this |
| `trend_sma` | `50` | 0 to 400 (step 1) | yes | Only buy above this SMA; 0 disables the filter |
| `max_hold` | `10` | 1 to 100 (step 1) | yes | Exit after this many bars in the trade |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.rsi_oversold`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
id = "signal.rsi_oversold"
with = { rsi_period = 4, entry = 25, exit = 60, trend_sma = 50, max_hold = 10 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat, RSI(`rsi_period`) is below `entry` and the close is above the trend SMA, and a `SELL` of the whole position when RSI is above `exit` or `max_hold` bars have passed since the fill. Long-only, one position at a time.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 14 fills
  BUY  801 @ 1185.83 (bar 50)
  SELL 801 @ 1209.53 (bar 54)
  BUY  801 @ 1185.47 (bar 180)
fill_delay=1: 14 fills
  BUY  801 @ 1180.08 (bar 51)
  SELL 801 @ 1214.60 (bar 55)
  BUY  801 @ 1184.16 (bar 181)
```

Trades are short (the demo's first round trip lasts a few bars) and the first `BUY` waits for the 50-bar trend SMA.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- Parameter-sweep overfitting: five sweepable params (`rsi_period`, `entry`, `exit`, `trend_sma`, `max_hold`). RSI thresholds and periods are classic over-optimised numbers; many combinations give a high win rate in-sample. Judge a tuned set by out-of-sample and walk-forward results, and by whether neighbouring values also work.
- No price stop, only a time stop: a position is closed on RSI recovery or after `max_hold` bars, never because it lost a given amount. In a falling market the dip you buy keeps dipping, and one gap-down or crash day can wipe out many small wins. Mean reversion tends to show a high win rate with a fat left tail; look at the worst trade and the drawdown, not the win rate.
- Lookahead / fill timing: every decision uses the current bar's close, and sizing uses that close too (`whole_shares(capital, allocation, bar.close)`). `replay(fill_delay=0)` then fills at that same close, which you cannot do live (the close is only known once the session is over). The realistic model is the next bar's open (`fill_delay=1`, and the engine's `NextOpenExecution`); in the snippet above it moves fills, e.g. the first BUY 1185.83 becomes 1180.08 and the first SELL 1209.53 becomes 1214.60. The quantity was sized at the old close, so a gap up can also overshoot `capital * allocation`. For a short-horizon dip-buyer that drift is a big part of the expected gain, and the 'buy the close of the oversold bar' fill is the most optimistic assumption in the test.
- Cost sensitivity: average gains per trade are small and the holding period is short, so the round-trip costs (STT, GST, stamp duty, spread) are a large share of the edge. A gross backtest overstates; run with the cost pack.
- Trend filter caveat: `close > SMA(trend_sma)` helps avoid some falling knives but lags. Setting `trend_sma = 0` removes the filter entirely and turns this into a pure dip-buyer, which is not the same strategy as the shipped config.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Sizing and risk: the position is `floor(capital * allocation / close)` with the fixed `capital` param. Profits and losses are not compounded back in, and the default 95% allocation to one instrument means any single trade can move the whole account.
