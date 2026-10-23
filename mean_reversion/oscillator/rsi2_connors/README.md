# rsi2_connors

Long-only RSI(2) mean reversion. Buy RSI(2) <= `oversold` while above the trend SMA; exit once the close is above the short exit SMA. Frequent signals by design.

- **Category:** mean reversion / oscillator
- **Timeframe:** daily bars (any bar size works)
- **Params** (`config.toml`): `oversold`, `trend_sma`, `exit_sma`, `capital`, `allocation`
- **Sizing:** whole shares, `floor(capital * allocation / close)`
- **Costs:** applied by the Honba backtest engine (STT, GST, stamp duty), not the strategy
- **Origin:** Ported from a Jesse example strategy (MIT)

Test: `pytest mean_reversion/oscillator/rsi2_connors` (needs `honba` on the path).

## Usage

Load it by registry name with `honba.strategies.loader` (`find_catalog` locates this checkout, `load_catalog_strategy` imports `strategy.py` and reads `config.toml`), then run it through the `honba.strategies.testing.replay` harness. This snippet is runnable from the repo root with `honba` installed:

```python
import math

from honba.domain import Bar, InstrumentId
from honba.strategies.loader import find_catalog, load_catalog_strategy
from honba.strategies.testing import replay

catalog = find_catalog(".")  # run from the honba-strategies checkout, or pass its path
cs = load_catalog_strategy(
    "rsi2_connors", catalog
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

To change parameters, update `cs.config.params` (for example `cs.config.params.update(oversold=5)`) before `cs.instantiate()`.

**Parameters** (`config.toml` values; bounds and sweepability from `step.toml`):

| Param | Default | Bounds | Sweepable | Meaning |
|---|---|---|---|---|
| `oversold` | `10` | 1 to 50 (step 1) | yes | Buy when RSI(2) is at or below this |
| `trend_sma` | `200` | 2 to 400 (step 1) | yes | Only buy above this SMA |
| `exit_sma` | `5` | 1 to 50 (step 1) | yes | Sell when the close is above this SMA |
| `capital` | `1000000` | 1000 to 10000000000 | no | INR available to the strategy |
| `allocation` | `0.95` | 0.01 to 1.0 (step 0.01) | no | Fraction of capital deployed per entry; the strategy requires 0 < allocation <= 1 |

**As a chain step.** `step.toml` registers it as `signal.rsi2_connors`, a standalone per-symbol signal (consumes `universe`, emits `orders`):

```toml
[[steps]]
id = "signal.rsi2_connors"
with = { oversold = 10, trend_sma = 200, exit_sma = 5 }
```

Chains that name catalog ids validate (`tools/validate_chain.py`) but are not runnable in `honba-examples` yet.

## Possible output

`on_bar` emits market orders for the one instrument in `config.toml`: a `BUY` of `floor(capital * allocation / close)` shares when flat, RSI(2) is at or below `oversold` and the close is above the trend SMA, and a `SELL` of the whole position once the close is above the short exit SMA. Long-only, one position at a time.

Real output of the snippet above, run on the synthetic series it builds (a sine wave plus drift, **not market data**, so it shows the mechanics only and says nothing about profitability). `fill_delay=0` fills at the signal bar's close, `fill_delay=1` at the next bar's open:

```text
fill_delay=0: 20 fills
  BUY  712 @ 1333.27 (bar 200)
  SELL 712 @ 1199.13 (bar 214)
  BUY  775 @ 1225.49 (bar 224)
fill_delay=1: 20 fills
  BUY  712 @ 1327.79 (bar 201)
  SELL 712 @ 1202.22 (bar 215)
  BUY  775 @ 1223.46 (bar 225)
```

The 200-bar trend SMA delays the first trade (here the first `BUY` is on bar 200). In this run the first round trip is `BUY` 1333.27, `SELL` 1199.13, a loss of about 10% on the synthetic series: the strategy has no stop, so a dip that keeps falling is held until the close finally clears the 5-bar SMA.

No recorded backtest yet (`backtest_result.json` has `status: pending`), so this README quotes no performance figures.

## Pitfalls

The points below are about *this* strategy's logic. For the general treatment (in-sample testing, survivorship, trading the close, data mining, ...) read [Avoiding backtest biases](https://honba-labs.github.io/honba/book/backtesting/avoiding_backtest_biases.html).

- No stop and no time exit: the only exit is the close rising above the short SMA. If price keeps falling the position stays open and the loss grows (the demo's first trade lost about 10%). The standard rationale is that deep oversold bars in an uptrend revert, but the losers are large and rare, so a high win rate can coexist with a poor expectancy. Look at the worst trade and the drawdown.
- Parameter-sweep overfitting: three sweepable params (`oversold` 1 to 50, `trend_sma` 2 to 400, `exit_sma` 1 to 50). RSI(2) is a very short window, and many threshold combinations look good by chance; keep to the published values unless a walk-forward test disagrees.
- Lookahead / fill timing: every decision uses the current bar's close, and sizing uses that close too (`whole_shares(capital, allocation, bar.close)`). `replay(fill_delay=0)` then fills at that same close, which you cannot do live (the close is only known once the session is over). The realistic model is the next bar's open (`fill_delay=1`, and the engine's `NextOpenExecution`); in the snippet above it moves fills, e.g. the first BUY 1333.27 becomes 1327.79 and the first SELL 1199.13 becomes 1202.22. The quantity was sized at the old close, so a gap up can also overshoot `capital * allocation`. This is a 'buy the worst close' strategy, so the fill assumption matters more than usual.
- Cost sensitivity: frequent short trades with a small average gain per trade. STT, GST, stamp duty and slippage take a large share of that gain. Report net results from the engine with costs on.
- Small and overlapping signals: signals cluster in volatile periods (crashes produce many oversold readings at once), so the trades are not independent and the sample size is smaller than the trade count suggests.
- Data: use split- and dividend-adjusted bars. An unadjusted split shows up as a fake gap and can trigger a false signal. The shipped config points at `NIFTY50`, an index: index levels are price-return (no dividends) and not directly tradable (you would trade an ETF or futures, with tracking error and roll costs). Pointing it at one stock chosen today adds survivorship bias (names that were delisted or fell out of the index never appear). Sizing and risk: the position is `floor(capital * allocation / close)` with the fixed `capital` param. Profits and losses are not compounded back in, and the default 95% allocation to one instrument means any single trade can move the whole account.
