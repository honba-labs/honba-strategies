"""Integration: catalog loader path, full Alpha 30 replay and config contract."""

import json
from pathlib import Path

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.markets.india.universes import resolve_universe
from honba.strategies.config import StrategyConfig
from honba.strategies.context import LedgerContext
from honba.strategies.loader import load_catalog_strategy
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
CATALOG = HERE.parent.parent.parent
DAY_NS = 86_400_000_000_000


def _bars(symbols, days=60):
    """Deterministic, symbol-dependent drifting prices (no RNG)."""
    out = []
    for d in range(days):
        for k, s in enumerate(symbols):
            p = (50.0 + 37.0 * k) * (1 + 0.004 * ((d * (k % 5 + 1)) % 11 - 5))
            out.append(Bar(InstrumentId(s, "NSE"), (d + 1) * DAY_NS, p, p, p, p, 1000.0))
    return out


def test_loads_through_the_catalog_loader():
    cs = load_catalog_strategy("equal_weight", CATALOG)
    strat = cs.instantiate()
    assert type(strat).__name__ == "EqualWeightRebalance"
    strat.bind(LedgerContext(cash=1_000_000.0))
    symbols = [i.symbol for i in resolve_universe("nifty200_alpha30")]
    result = replay(strat, _bars(symbols, days=20))
    assert len({f.instrument_id.symbol for f in result.fills}) == 30


def test_config_toml_documents_the_grammar():
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    assert cfg.params == {
        "universe": "nifty200_alpha30",
        "weighting": "equal",
        "schedule": "every:15d",
        "allocation": 0.995,
    }
    assert json.loads((HERE / "backtest_result.json").read_text())
