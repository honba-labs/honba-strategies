from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
CLS = "DonchianTrend"


def build(load_strategy, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return getattr(mod, CLS)(cfg), cfg


def ohlc(rows, symbol="NIFTY50"):
    """Bars from (high, low, close) rows; open = close."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, h, l, c, 1000.0) for i, (h, l, c) in enumerate(rows)]


SMALL = dict(period=3, trend_sma=3, capital=1000.0, allocation=1.0)


def test_buys_breakout_and_exits_below_channel_low(load_strategy, make_bars):
    s, cfg = build(load_strategy, **SMALL)
    closes = [10, 10, 10, 10, 11, 12, 13, 9, 8, 7]
    result = replay(s, make_bars(closes, cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert (result.fills[0].ts, result.fills[0].price, result.fills[0].quantity) == (5, 11, 90)
    assert (result.fills[1].ts, result.fills[1].quantity) == (8, 90)
    assert s.position(cfg.instrument_id) == 0


def test_no_trade_before_warmup(load_strategy, make_bars):
    s, cfg = build(load_strategy, period=50, trend_sma=50)
    result = replay(s, make_bars([100 + i for i in range(30)], cfg.symbol))
    assert result.fills == []


@pytest.mark.parametrize("bad", [dict(period=0), dict(trend_sma=0), dict(capital=-1)])
def test_rejects_bad_params(load_strategy, bad):
    with pytest.raises(ValueError):
        build(load_strategy, **bad)
