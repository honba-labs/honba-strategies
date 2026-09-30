from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
CLS = "KdjCross"


def build(load_strategy, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return getattr(mod, CLS)(cfg), cfg


def ohlc(rows, symbol="NIFTY50"):
    """Bars from (high, low, close) rows; open = close."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, h, l, c, 1000.0) for i, (h, l, c) in enumerate(rows)]


SMALL = dict(fastk=3, slowk=2, slowd=2, atr_period=3, atr_mult=2.0, capital=1000.0, allocation=1.0)


def test_buys_when_j_above_k_and_d_and_exits_when_j_turns_down(load_strategy, make_bars):
    s, cfg = build(load_strategy, **SMALL)
    closes = [10, 10, 10, 10, 10, 11, 12, 13, 14, 13, 12]
    result = replay(s, make_bars(closes, cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert (result.fills[0].ts, result.fills[0].price, result.fills[0].quantity) == (6, 11, 90)
    assert result.fills[1].ts == 8  # in profit and J falls from its peak
    assert s.position(cfg.instrument_id) == 0


def test_atr_stop_exits_intrabar(load_strategy):
    s, cfg = build(load_strategy, **{**SMALL, "atr_mult": 0.001})
    rows = [(c, c, c) for c in [10, 10, 10, 10, 10, 11]] + [(12, 10.9, 12), (13, 13, 13)]
    result = replay(s, ohlc(rows, cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert result.fills[1].ts == 7  # low 10.9 pierces the stop while J is still rising


def test_no_trade_before_warmup(load_strategy, make_bars):
    s, cfg = build(load_strategy, fastk=30)
    result = replay(s, make_bars([100 + i for i in range(20)], cfg.symbol))
    assert result.fills == []


def test_kdj_values_on_known_series(load_strategy):
    mod = load_strategy(HERE)
    k = mod.Kdj(3, 2, 2)
    out = [k.update(c, c, c) for c in [10, 10, 10, 10, 10, 11]]
    assert out[:4] == [None, None, None, None] or out[-1] is not None
    kk, dd, jj = out[-1]
    assert (kk, dd, jj) == (50.0, 25.0, 100.0)


@pytest.mark.parametrize("bad", [dict(fastk=0), dict(slowk=0), dict(slowd=0), dict(atr_period=0),
                                 dict(atr_mult=0), dict(allocation=0)])
def test_rejects_bad_params(load_strategy, bad):
    with pytest.raises(ValueError):
        build(load_strategy, **bad)


def test_kdj_smoothing_and_atr_are_configurable(load_strategy):
    s, _ = build(load_strategy, atr_first_bar=True, slowk_ma="ema", slowd_ma="wma")
    assert s._atr.include_first_bar is True
    assert type(s._kdj._k).__name__ == "Ema" and type(s._kdj._d).__name__ == "Wma"
    with pytest.raises(ValueError):
        build(load_strategy, slowk_ma="nope")
