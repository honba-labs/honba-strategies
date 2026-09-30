from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent


def build(load_strategy, indicator=None, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    cfg.indicators["trend"].update(indicator or {})
    return mod.SupertrendFollow(cfg), cfg


def ohlc(closes, symbol="NIFTY50"):
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, c + 1, c - 1, c, 1000.0) for i, c in enumerate(closes)]


SMALL = dict(atr_period=3, factor=1.5)
UP_THEN_CRASH = [100 + 2 * i for i in range(15)] + [128 - 6 * i for i in range(1, 8)]


def test_config_declares_the_indicator(load_strategy):
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    assert cfg.indicators["trend"]["kind"] == "supertrend"


def test_buys_in_uptrend_and_sells_when_it_flips(load_strategy):
    s, cfg = build(load_strategy, SMALL, capital=100_000.0, allocation=1.0)
    result = replay(s, ohlc(UP_THEN_CRASH, cfg.symbol))
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    buy, sell = result.fills
    # Supertrend(3, 1.5) starts in a downtrend, flips up on bar 6 (close 110) and down on bar 16 (close 122)
    assert (buy.ts, buy.price, buy.quantity) == (6, 110, 909)  # floor(100000 / 110)
    assert (sell.ts, sell.price, sell.quantity) == (16, 122, 909)
    assert s.position(cfg.instrument_id) == 0


def test_no_trade_during_warmup(load_strategy):
    s, cfg = build(load_strategy)  # default atr_period 10
    assert replay(s, ohlc([100 + i for i in range(5)], cfg.symbol)).fills == []


def test_indicator_parameters_come_from_config(load_strategy):
    fast, cfg = build(load_strategy, {"atr_period": 3, "factor": 1.0})
    slow, _ = build(load_strategy, {"atr_period": 3, "factor": 5.0})
    bars = ohlc(UP_THEN_CRASH, cfg.symbol)
    sell_fast = replay(fast, bars).fills[-1].ts
    sell_slow = replay(slow, bars).fills
    assert sell_fast < (sell_slow[-1].ts if len(sell_slow) > 1 else 10**9)  # wider stop exits later or never


def test_invalid_config(load_strategy):
    with pytest.raises(ValueError):
        build(load_strategy, capital=0)
    with pytest.raises(ValueError):
        build(load_strategy, allocation=1.5)
    with pytest.raises(ValueError):
        build(load_strategy, {"factor": -1})
