"""Strategy: alpha30_low_vol

Selects the 15 lowest-volatility constituents from the Alpha-30 universe and holds them equal-weighted.
"""

from __future__ import annotations

from honba.strategies.config import StrategyConfig
from honba.strategies.portfolio.factory import build_portfolio_strategy
from honba.strategies.portfolio.strategy import PortfolioStrategy


class Alpha30LowVol(PortfolioStrategy):
    name = "alpha30_low_vol"

    def __init__(self, config: StrategyConfig) -> None:
        params = {"universe": "nifty200_alpha30", "exchange": config.exchange, **config.params}
        parts = build_portfolio_strategy(params, name=self.name)
        super().__init__(
            parts.universe_source,
            parts.weighting,
            parts.schedule,
            parts.selector,
            allocation=parts.allocation,
            name=self.name,
            history_len=parts.history_len,
        )
