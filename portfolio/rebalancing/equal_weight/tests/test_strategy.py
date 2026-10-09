"""Unit tests for EqualWeightRebalance (ported from the retired Alpha30EqualWeight tests)."""

import time
from pathlib import Path

import pytest
from honba.entities import Money
from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.markets.india import universes
from honba.strategies.config import StrategyConfig
from honba.strategies.context import LedgerContext
from honba.strategies.portfolio.schedule import EveryNDays
from honba.strategies.portfolio.strategy import PortfolioStrategy
from honba.strategies.portfolio.universe import NamedUniverse
from honba.strategies.portfolio.weighting import EqualWeight
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
DAY_NS = 86_400_000_000_000


@pytest.fixture
def mod(load_strategy):
    return load_strategy(HERE)


def _cfg(**params):
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    return cfg


def _bars(symbols, prices):
    return [
        Bar(InstrumentId(s, "NSE"), (i + 1) * DAY_NS, p, p, p, p, 1000.0)
        for i, p in enumerate(prices)
        for s in symbols
    ]


def _universe_cfg(symbols, **params):
    return _cfg(universe=list(symbols), **params)


def test_is_a_thin_portfolio_strategy(mod):
    strat = mod.EqualWeightRebalance(_cfg())
    assert isinstance(strat, PortfolioStrategy)
    assert strat.name == "equal_weight_rebalance"
    assert isinstance(strat.universe_source, NamedUniverse)
    assert strat.universe_source.name == "nifty200_alpha30"
    assert isinstance(strat.weighting, EqualWeight)
    assert isinstance(strat.schedule, EveryNDays)
    assert strat.allocation == 0.995


def test_initialization_resolves_alpha30(mod):
    strat = mod.EqualWeightRebalance(_cfg())
    strat.on_start()
    assert len(list(strat.universe())) == 30


def test_entries_are_placed_in_symbol_order(mod):
    symbols = ["MCX", "BHEL", "HINDALCO"]
    strat = mod.EqualWeightRebalance(_universe_cfg(symbols, schedule="every:3d"))
    strat.bind(LedgerContext(cash=300_000.0))
    result = replay(strat, _bars(symbols, [100.0, 105.0, 110.0]))
    buys = [f for f in result.fills if f.side == OrderSide.BUY]
    assert [f.instrument_id.symbol for f in buys[:3]] == sorted(symbols)


def test_cash_is_money_and_sizing_uses_major_units(mod):
    symbols = ["BHEL", "MCX"]
    strat = mod.EqualWeightRebalance(_universe_cfg(symbols))
    strat.bind(LedgerContext(cash=300_000.0))
    assert isinstance(strat.ctx.cash(), Money)
    result = replay(strat, _bars(symbols, [100.0, 100.0]))
    buys = [f for f in result.fills if f.side == OrderSide.BUY]
    assert [f.quantity for f in buys] == [1492.0, 1492.0]


def test_universe_comes_from_config(mod):
    strat = mod.EqualWeightRebalance(_cfg(universe="nifty50"))
    strat.on_start()
    assert len(list(strat.universe())) == len(universes.UNIVERSES["nifty50"])


def test_unknown_universe_raises_instead_of_using_a_seed(mod):
    # The old strategy fell back to a hard-coded seed; the core never guesses membership.
    strat = mod.EqualWeightRebalance(_cfg(universe="no_such_universe"))
    with pytest.raises(ValueError):
        strat.on_start()
        list(strat.universe())


def test_unknown_param_is_rejected(mod):
    with pytest.raises(ValueError, match="rebalance_days"):
        mod.EqualWeightRebalance(_cfg(rebalance_days=15))


def test_weights_are_equal_within_one_share(mod):
    symbols = ["A", "B", "C", "D"]
    prices = {"A": 50.0, "B": 123.0, "C": 987.0, "D": 4321.0}
    strat = mod.EqualWeightRebalance(_universe_cfg(symbols))
    strat.bind(LedgerContext(cash=1_000_000.0))
    bars = [Bar(InstrumentId(s, "NSE"), DAY_NS, p, p, p, p, 1000.0) for s, p in prices.items()]
    replay(strat, bars)
    target = 1_000_000.0 * 0.995 / len(symbols)
    for s, p in prices.items():
        held = strat.position(InstrumentId(s, "NSE"))
        assert 0 <= target - held * p < p  # floor to whole shares, never over target


def test_rebalances_only_on_cadence_days(mod):
    strat = mod.EqualWeightRebalance(_universe_cfg(["A", "B"], schedule="every:3d"))
    strat.bind(LedgerContext(cash=100_000.0))
    # B moves every day, so any off-cadence rebalance would show up as an extra fill day.
    b_close = [100.0, 130.0, 140.0, 150.0, 170.0, 180.0, 190.0, 190.0]
    bars = []
    for d, pb in enumerate(b_close):
        for s, p in (("A", 100.0), ("B", pb)):
            bars.append(Bar(InstrumentId(s, "NSE"), (d + 1) * DAY_NS, p, p, p, p, 1000.0))
    result = replay(strat, bars)
    assert sorted({f.ts // DAY_NS for f in result.fills}) == [1, 4, 7]


def test_leavers_are_exited_and_joiners_entered(mod, monkeypatch):
    monkeypatch.setitem(universes.UNIVERSES, "test_basket", ("A", "B", "C"))
    strat = mod.EqualWeightRebalance(_cfg(universe="test_basket", schedule="every:2d"))
    strat.bind(LedgerContext(cash=300_000.0))
    bars = _bars(["A", "B", "C", "D"], [100.0] * 6)
    original = strat.on_bar
    seen_days: set[int] = set()

    def swap_membership(bar):
        seen_days.add(bar.ts // DAY_NS)
        if len(seen_days) == 3:  # from day 3 on: C leaves, D joins
            universes.UNIVERSES["test_basket"] = ("A", "B", "D")
        original(bar)

    monkeypatch.setattr(strat, "on_bar", swap_membership)
    replay(strat, bars)
    ids = {s: InstrumentId(s, "NSE") for s in "ABCD"}
    assert strat.position(ids["C"]) == 0  # exited
    assert strat.position(ids["D"]) > 0  # entered
    assert strat.position(ids["A"]) == pytest.approx(strat.position(ids["B"]), abs=1)
    assert strat.position(ids["D"]) == pytest.approx(strat.position(ids["A"]), abs=1)


def test_no_wall_clock_is_consulted(mod, monkeypatch):
    def boom(*a, **k):
        raise AssertionError("wall clock used")

    monkeypatch.setattr(time, "time", boom)
    monkeypatch.setattr(time, "time_ns", boom)
    symbols = ["A", "B"]
    strat = mod.EqualWeightRebalance(_universe_cfg(symbols, schedule="every:2d"))
    strat.bind(LedgerContext(cash=100_000.0))
    result = replay(strat, _bars(symbols, [100.0, 101.0, 102.0, 103.0]))
    assert result.fills
