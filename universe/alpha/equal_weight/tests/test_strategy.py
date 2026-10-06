from pathlib import Path

import pytest
from honba.domain.bar import Bar
from honba.domain.instrument import InstrumentId
from honba.domain.order import OrderSide
from honba.entities import Money
from honba.markets.india import universes
from honba.strategies.config import StrategyConfig
from honba.strategies.context import LedgerContext
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


def test_initialization_resolves_alpha30(mod):
    strat = mod.Alpha30EqualWeight(_cfg())
    strat.on_start()
    assert len(strat.universe) == 30
    assert strat.rebalance_days == 15


def test_entries_are_placed_in_symbol_order(mod, monkeypatch):
    symbols = ["MCX", "BHEL", "HINDALCO"]
    strat = mod.Alpha30EqualWeight(_cfg(capital=300_000.0, rebalance_days=3))
    members = {InstrumentId(s, "NSE") for s in symbols}
    monkeypatch.setattr(mod, "_resolve", lambda *a, **k: set(members))
    strat.bind(LedgerContext(cash=300_000.0))
    strat.on_start()
    result = replay(strat, _bars(symbols, [100.0, 105.0, 110.0]))
    buys = [f for f in result.fills if f.side == OrderSide.BUY]
    first = [f.instrument_id.symbol for f in buys[:3]]
    assert first == sorted(symbols)


def test_cash_is_money_and_sizing_uses_major_units(mod, monkeypatch):
    strat = mod.Alpha30EqualWeight(_cfg(capital=300_000.0))
    symbols = ["BHEL", "MCX"]
    members = {InstrumentId(s, "NSE") for s in symbols}
    monkeypatch.setattr(mod, "_resolve", lambda *a, **k: set(members))
    strat.bind(LedgerContext(cash=300_000.0))
    strat.on_start()
    assert isinstance(strat.ctx.cash(), Money)
    result = replay(strat, _bars(symbols, [100.0, 100.0]))
    buys = [f for f in result.fills if f.side == OrderSide.BUY]
    assert [f.quantity for f in buys] == [1492.0, 1492.0]


def test_universe_comes_from_config(mod):
    strat = mod.Alpha30EqualWeight(_cfg(universe_name="nifty50"))
    strat.on_start()
    assert len(strat.universe) == len(universes.UNIVERSES["nifty50"])


def test_seed_is_used_when_default_universe_unregistered(mod, monkeypatch):
    monkeypatch.delitem(universes.UNIVERSES, "nifty200_alpha30")
    strat = mod.Alpha30EqualWeight(_cfg())
    strat.on_start()
    assert {i.symbol for i in strat.universe} == set(mod._SEED)


def test_bar_day_without_timestamp_raises(mod):
    class NoTs:
        pass

    with pytest.raises(ValueError, match="timestamp"):
        mod._bar_day(NoTs(), 0)


def test_bar_day_uses_event_timestamp(mod):
    bar = Bar(InstrumentId("BHEL", "NSE"), 3 * DAY_NS, 1.0, 1.0, 1.0, 1.0, 1.0)
    assert mod._bar_day(bar, 0).isoformat() == "1970-01-04"
