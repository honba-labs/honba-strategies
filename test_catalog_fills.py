"""Every catalog strategy must behave with delayed (live-like) fills."""
import inspect
import json
import math
from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

ROOT = Path(__file__).resolve().parent
DIRS = [
    ROOT / e["path"]
    for e in json.loads((ROOT / "registry.json").read_text())["strategies"]
    if not e["path"].startswith("universe/alpha")
]


def wave_bars(symbol):
    iid = InstrumentId(symbol, "NSE")
    bars = []
    for i in range(600):
        c = 1000 + 250 * math.sin(i / 25) + 60 * math.sin(i / 4.3) + i * 0.2
        o = 1000 + 250 * math.sin((i - 1) / 25) + 60 * math.sin((i - 1) / 4.3) + (i - 1) * 0.2
        bars.append(Bar(iid, i + 1, o, max(o, c) * 1.01, min(o, c) * 0.99, c, 1e6))
    return bars


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
@pytest.mark.parametrize("delay", [0, 1, 2])
def test_no_duplicate_orders_with_delayed_fills(d, delay, load_strategy):
    mod = load_strategy(d)
    cls = next(
        c for _, c in inspect.getmembers(mod, inspect.isclass)
        if issubclass(c, Strategy) and c is not Strategy and c.__module__ == mod.__name__
    )
    cfg = StrategyConfig.from_toml(d / "config.toml")
    s = cls(cfg)
    result = replay(s, wave_bars(cfg.symbol), fill_delay=delay)
    assert result.fills, f"{d.name} never traded on the wave series"
    position = 0.0
    for f in result.fills:
        position += f.quantity if f.side is OrderSide.BUY else -f.quantity
        assert position >= -1e-9, "went short"
    sides = [f.side for f in result.fills]
    assert all(a != b for a, b in zip(sides, sides[1:])), "consecutive same-side orders"
