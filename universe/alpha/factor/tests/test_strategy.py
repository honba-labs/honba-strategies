from pathlib import Path
import pytest

from honba.domain.bar import Bar
from honba.domain.instrument import InstrumentId
from honba.domain.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent


def test_alpha30_factor_initialization(load_strategy):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    strat = mod.Alpha30Factor(cfg)
    assert strat.name == "alpha30_factor"
    assert len(strat.universe) == 30
    assert strat.rebalance_days == 15
    assert strat.capital == 1_000_000.0


def test_alpha30_factor_equal_weight_and_rebalance(load_strategy):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params["rebalance_days"] = 3
    cfg.params["capital"] = 300_000.0
    strat = mod.Alpha30Factor(cfg)

    symbols = ["HINDALCO", "BHEL", "MCX"]
    strat.universe = [InstrumentId(s, "NSE") for s in symbols]

    # Generate 6 bars (2 periods of 3 days)
    bars = []
    prices = [100.0, 105.0, 110.0, 120.0, 115.0, 125.0]
    for i, p in enumerate(prices):
        ts = (i + 1) * 86_400_000_000_000
        for s in symbols:
            bars.append(Bar(InstrumentId(s, "NSE"), ts, p, p, p, p, 1000.0))

    result = replay(strat, bars)
    # On day 1 (open-day 1), it enters all 3 equities
    day1_fills = [f for f in result.fills if f.ts == bars[0].ts]
    assert len(day1_fills) == 3
    assert all(f.side == OrderSide.BUY for f in day1_fills)

    # On day 4 (open-day 4 = 1st day of next 3-day cycle), it rebalances
    day4_fills = [f for f in result.fills if f.ts == 4 * 86_400_000_000_000]
    assert len(day4_fills) > 0
