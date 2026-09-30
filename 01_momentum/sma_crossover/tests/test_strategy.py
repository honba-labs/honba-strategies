from pathlib import Path

from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent


def build(load_strategy, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return mod.SmaCrossover(cfg), cfg


def test_buys_when_fast_above_slow_and_sells_on_cross_down(load_strategy, make_bars):
    s, cfg = build(load_strategy, fast=2, slow=4, capital=1000.0, allocation=1.0)
    closes = [10, 10, 10, 10, 11, 12, 13, 12, 9, 8, 7]
    result = replay(s, make_bars(closes, cfg.symbol))
    sides = [f.side for f in result.fills]
    assert sides == [OrderSide.BUY, OrderSide.SELL]
    assert s.position(cfg.instrument_id) == 0
    assert result.fills[0].quantity == 90  # floor(1000 / 11)
    assert result.fills[1].quantity == 90  # full exit


def test_no_trade_before_warmup(load_strategy, make_bars):
    s, cfg = build(load_strategy, fast=2, slow=50)
    result = replay(s, make_bars([100 + i for i in range(10)], cfg.symbol))
    assert result.fills == []


def test_rejects_fast_not_below_slow(load_strategy):
    import pytest

    with pytest.raises(ValueError):
        build(load_strategy, fast=50, slow=20)
