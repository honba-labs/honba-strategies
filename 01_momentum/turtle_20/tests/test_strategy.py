from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
CLS = "Turtle20"


def build(load_strategy, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return getattr(mod, CLS)(cfg), cfg


def ohlc(rows, symbol="NIFTY50"):
    """Bars from (high, low, close) rows; open = close."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, h, l, c, 1000.0) for i, (h, l, c) in enumerate(rows)]


SMALL = dict(entry=3, exit=2, atr_period=3, atr_mult=2.0, capital=1000.0, allocation=1.0)


def test_buys_entry_breakout_and_exits_on_exit_channel(load_strategy, make_bars):
    s, cfg = build(load_strategy, **SMALL)
    closes = [10, 10, 10, 10, 12, 13, 14, 13, 12, 9, 8]
    result = replay(s, make_bars(closes, cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert (result.fills[0].ts, result.fills[0].price, result.fills[0].quantity) == (5, 12, 83)
    assert (result.fills[1].ts, result.fills[1].price) == (9, 12)


def test_protective_atr_stop_exits_intrabar(load_strategy):
    s, cfg = build(load_strategy, **SMALL)
    rows = [(10, 10, 10)] * 4 + [(12, 12, 12), (12, 10, 11.5), (12, 11, 12)]
    result = replay(s, ohlc(rows, cfg.symbol))
    # ATR(3) at entry = 2/3, stop = 12 - 4/3 = 10.67; bar 6 low of 10 pierces it.
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert result.fills[1].ts == 6


def test_no_trade_before_warmup(load_strategy, make_bars):
    s, cfg = build(load_strategy)
    result = replay(s, make_bars([100 + i for i in range(15)], cfg.symbol))
    assert result.fills == []


@pytest.mark.parametrize("bad", [dict(entry=0), dict(exit=0), dict(atr_period=0), dict(atr_mult=0), dict(allocation=2)])
def test_rejects_bad_params(load_strategy, bad):
    with pytest.raises(ValueError):
        build(load_strategy, **bad)
