"""Shared test helpers for catalog strategies.

Requires ``honba`` on the path (``pip install -e honba/python`` or PYTHONPATH).
"""
import importlib.util
from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId


@pytest.fixture
def load_strategy():
    """Load ``<strategy dir>/strategy.py`` under a unique module name."""

    def _load(strategy_dir):
        import sys
        d = Path(strategy_dir).resolve()
        strategies_root = Path(__file__).resolve().parent
        for p in (d, d.parent, d.parent.parent, strategies_root):
            if str(p) not in sys.path:
                sys.path.insert(0, str(p))
        spec = importlib.util.spec_from_file_location(f"catalog_{d.name}", d / "strategy.py")
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    return _load


@pytest.fixture
def make_bars():
    """Bars from a list of closes (high=low=open=close) for a symbol on NSE."""

    def _make(closes, symbol="NIFTY50"):
        iid = InstrumentId(symbol, "NSE")
        return [Bar(iid, i + 1, c, c, c, c, 1000.0) for i, c in enumerate(closes)]

    return _make
