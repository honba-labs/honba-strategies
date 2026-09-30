from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
CLS = "Ifr2"


def build(load_strategy, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return getattr(mod, CLS)(cfg), cfg


def ohlc(rows, symbol="NIFTY50"):
    """Bars from (high, low, close) rows; open = close."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, h, l, c, 1000.0) for i, (h, l, c) in enumerate(rows)]


SMALL = dict(oversold=10, tenkan=2, kijun=3, senkou_b=4, displacement=11,  # cloud lags displacement-1 = 10 bars
              capital=1000.0, allocation=1.0)
RAMP_THEN_DIP = [100 + i for i in range(40)] + [135, 131]


def test_buys_rsi2_dip_above_cloud_and_exits_above_prior_two_highs(load_strategy, make_bars):
    s, cfg = build(load_strategy, **SMALL)
    result = replay(s, make_bars(RAMP_THEN_DIP + [140], cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert (result.fills[0].ts, result.fills[0].price, result.fills[0].quantity) == (42, 131, 7)
    assert result.fills[1].ts == 43


def test_no_entry_below_cloud(load_strategy, make_bars):
    s, cfg = build(load_strategy, **{**SMALL, "displacement": 1})
    result = replay(s, make_bars(RAMP_THEN_DIP, cfg.symbol))
    assert result.fills == []


def test_holds_until_close_clears_both_prior_highs(load_strategy, make_bars):
    s, cfg = build(load_strategy, **SMALL)
    result = replay(s, make_bars(RAMP_THEN_DIP + [132, 130, 136], cfg.symbol))
    # 132 clears the prior 131 high but not the 135 high; 130 clears neither; 136 does.
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert result.fills[1].ts == 45


def test_no_trade_before_warmup(load_strategy, make_bars):
    s, cfg = build(load_strategy)
    result = replay(s, make_bars([100 - i for i in range(30)], cfg.symbol))
    assert result.fills == []


@pytest.mark.parametrize("bad", [dict(oversold=0), dict(oversold=100), dict(tenkan=0), dict(kijun=0),
                                 dict(senkou_b=0), dict(displacement=0), dict(allocation=0)])
def test_rejects_bad_params(load_strategy, bad):
    with pytest.raises(ValueError):
        build(load_strategy, **bad)
