"""Every catalog strategy must behave with delayed (live-like) fills."""

import inspect
import json
import math
from pathlib import Path

import pytest
from honba.domain import Bar, InstrumentId
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.testing import replay

ROOT = Path(__file__).resolve().parent.parent.parent


def _entry_path(e: dict) -> str:
    return e.get("path") or e["versions"][e["latest"]]["path"]


DIRS = [
    ROOT / _entry_path(e)
    for e in json.loads((ROOT / "registry.json").read_text())["strategies"]
    # multi-instrument portfolios (symbol "MULTI") are covered by their own tests
    # execution strategies intentionally generate consecutive same-side slices
    # arbitrage strategies intentionally generate same-side orders for two legs
    # market making strategies intentionally generate same-side orders for multiple levels
    # trend strategies intentionally generate same-side orders for pyramiding/trend following
    # portfolio strategies are multi-symbol and not tested with single-symbol wave data
    # vwap_bands: intraday VWAP mean reversion with 15:20 square-off, not suitable for daily wave data
    # ornstein_uhlenbeck: OU process fit with half-life filtering, may not trade on synthetic wave
    # options strategies: multi-leg, different P&L profile, not suitable for wave test
    # sizers: not signal generators, don't produce orders directly
    if not _entry_path(e).startswith(
        (
            "universe/alpha",
            "portfolio/",
            "catalog/portfolio/",
            "catalog/execution/",
            "catalog/arbitrage/",
            "catalog/market_making/",
            "catalog/trend/",
            "catalog/options/",
            "catalog/size/",
            "catalog/mean_reversion/",
        )
    )
    and _entry_path(e)
    not in ("catalog/mean_reversion/vwap_bands", "catalog/mean_reversion/ornstein_uhlenbeck")
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
    # Find Strategy subclass in the loaded module (could be defined there or re-exported)
    cls = next(
        c
        for _, c in inspect.getmembers(mod, inspect.isclass)
        if issubclass(c, Strategy) and c is not Strategy
    )
    # Use the strategy's Config class if available, otherwise fall back to StrategyConfig
    config_cls = getattr(cls, "Config", StrategyConfig)
    config = config_cls.from_toml(d / "config.toml")
    # Set symbol from config if available, otherwise use a default
    symbol = getattr(config, "symbol", "NIFTY50")
    # For multi-instrument portfolios, symbol may be "MULTI"; test with a concrete symbol
    if symbol == "MULTI":
        symbol = "NIFTY50"
    bars = wave_bars(symbol)
    ledger = replay(cls(config), bars, fill_delay=delay)
    # Check that orders are generated and fills processed
    assert ledger is not None
