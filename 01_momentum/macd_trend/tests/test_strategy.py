from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
CLS = "MacdTrend"


def build(load_strategy, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return getattr(mod, CLS)(cfg), cfg


def ohlc(rows, symbol="NIFTY50"):
    """Bars from (high, low, close) rows; open = close."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, h, l, c, 1000.0) for i, (h, l, c) in enumerate(rows)]


SMALL = dict(ema=3, fastperiod=2, slowperiod=4, signal=2, capital=1000.0, allocation=1.0)


def test_buys_in_uptrend_and_exits_when_macd_and_price_weaken(load_strategy, make_bars):
    s, cfg = build(load_strategy, **SMALL)
    closes = [10] * 8 + [11, 12, 13, 14, 15] + [10, 8, 6, 4, 2, 1]
    result = replay(s, make_bars(closes, cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert result.fills[0].quantity == result.fills[1].quantity
    assert result.fills[0].ts < result.fills[1].ts
    assert result.fills[1].price < result.fills[0].price
    assert s.position(cfg.instrument_id) == 0


def test_no_trade_before_warmup(load_strategy, make_bars):
    s, cfg = build(load_strategy)
    result = replay(s, make_bars([100 + i for i in range(30)], cfg.symbol))
    assert result.fills == []


@pytest.mark.parametrize("bad", [dict(ema=0), dict(fastperiod=26, slowperiod=12), dict(signal=0), dict(allocation=0)])
def test_rejects_bad_params(load_strategy, bad):
    with pytest.raises(ValueError):
        build(load_strategy, **bad)
