from pathlib import Path

from honba.domain.bar import Bar
from honba.domain.instrument import InstrumentId
from honba.strategies.config import StrategyConfig
from honba.strategies.context import LedgerContext
from honba.strategies.portfolio.selection import SelectAll
from honba.strategies.portfolio.strategy import PortfolioStrategy
from honba.strategies.portfolio.universe import NamedUniverse
from honba.strategies.portfolio.weighting import EqualWeight
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent


def test_alpha30_momentum_initialization(load_strategy):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    strat = mod.Alpha30Momentum(cfg)
    assert isinstance(strat, PortfolioStrategy)
    assert strat.name == "alpha30_momentum"
    assert isinstance(strat.universe_source, NamedUniverse)
    assert strat.universe_source.name == "nifty200_alpha30"
    assert isinstance(strat.weighting, EqualWeight)
    assert strat.allocation == 0.98
    assert not isinstance(strat.selector, SelectAll)  # config has a select rule


def test_alpha30_momentum_rebalance(load_strategy):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params["schedule"] = "every:3d"
    cfg.params["select"] = (
        "top:2:momentum:2"  # short lookback: the replay has only 6 bars
    )
    strat = mod.Alpha30Momentum(cfg)
    strat.bind(LedgerContext(cash=1_000_000.0))

    symbols = ["HINDALCO", "BHEL", "MCX"]
    bars = []
    prices = [100.0, 105.0, 110.0, 120.0, 115.0, 125.0]
    for i, p in enumerate(prices):
        ts = (i + 1) * 86_400_000_000_000
        for s in symbols:
            bars.append(Bar(InstrumentId(s, "NSE"), ts, p, p, p, p, 1000.0))

    result = replay(strat, bars)
    assert len(result.fills) > 0
