from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
CLS = "BollingerBreakout"


def build(load_strategy, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return getattr(mod, CLS)(cfg), cfg


def ohlc(rows, symbol="NIFTY50"):
    """Bars from (high, low, close) rows; open = close."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, h, l, c, 1000.0) for i, (h, l, c) in enumerate(rows)]


SMALL = dict(period=10, mult=2.0, tenkan=2, kijun=3, senkou_b=4, displacement=1,
             capital=1000.0, allocation=1.0)


def test_buys_upper_band_breakout_and_exits_below_middle(load_strategy, make_bars):
    s, cfg = build(load_strategy, **SMALL)
    closes = [10] * 12 + [15, 16, 17, 9]
    result = replay(s, make_bars(closes, cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert (result.fills[0].ts, result.fills[0].price, result.fills[0].quantity) == (13, 15, 66)
    assert (result.fills[1].ts, result.fills[1].quantity) == (16, 66)


def test_no_trade_before_warmup(load_strategy, make_bars):
    s, cfg = build(load_strategy)
    result = replay(s, make_bars([100] * 20 + [200], cfg.symbol))
    assert result.fills == []


@pytest.mark.parametrize("bad", [dict(period=1), dict(mult=0), dict(tenkan=0), dict(kijun=0),
                                 dict(senkou_b=0), dict(displacement=0), dict(capital=0)])
def test_rejects_bad_params(load_strategy, bad):
    with pytest.raises(ValueError):
        build(load_strategy, **bad)
