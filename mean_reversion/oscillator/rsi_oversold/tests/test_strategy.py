from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
CLS = "RsiOversold"


def build(load_strategy, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return getattr(mod, CLS)(cfg), cfg


def ohlc(rows, symbol="NIFTY50"):
    """Bars from (high, low, close) rows; open = close."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, h, l, c, 1000.0) for i, (h, l, c) in enumerate(rows)]


SMALL = dict(rsi_period=2, entry=30, exit=60, trend_sma=0, max_hold=10, capital=1000.0, allocation=1.0)


def test_buys_oversold_and_exits_when_rsi_recovers(load_strategy, make_bars):
    s, cfg = build(load_strategy, **SMALL)
    result = replay(s, make_bars([20, 19, 18, 17, 20, 25], cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert (result.fills[0].ts, result.fills[1].ts) == (3, 5)
    assert result.fills[0].quantity == result.fills[1].quantity == 55


def test_exits_after_max_hold_bars(load_strategy, make_bars):
    s, cfg = build(load_strategy, **{**SMALL, "max_hold": 3})
    result = replay(s, make_bars([20 - i for i in range(10)], cfg.symbol))
    assert [f.side for f in result.fills[:2]] == [OrderSide.BUY, OrderSide.SELL]
    assert (result.fills[0].ts, result.fills[1].ts) == (3, 6)


def test_trend_filter_blocks_falling_knife(load_strategy, make_bars):
    s, cfg = build(load_strategy, **{**SMALL, "trend_sma": 3})
    result = replay(s, make_bars([20 - i for i in range(10)], cfg.symbol))
    assert result.fills == []


def test_no_trade_before_warmup(load_strategy, make_bars):
    s, cfg = build(load_strategy, rsi_period=14, trend_sma=50)
    result = replay(s, make_bars([100 - i for i in range(10)], cfg.symbol))
    assert result.fills == []


@pytest.mark.parametrize("bad", [dict(rsi_period=0), dict(entry=60, exit=50), dict(trend_sma=-1),
                                 dict(max_hold=0), dict(allocation=0)])
def test_rejects_bad_params(load_strategy, bad):
    with pytest.raises(ValueError):
        build(load_strategy, **bad)
