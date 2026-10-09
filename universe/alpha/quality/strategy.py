"""Strategy: alpha30_quality

Equal-weight allocation across the quality-screened Nifty200 Alpha 30 universe, rebalancing every 29 days.
"""

from __future__ import annotations

from honba.strategies.config import StrategyConfig
from honba.strategies.portfolio.factory import build_portfolio_strategy
from honba.strategies.portfolio.strategy import PortfolioStrategy


class Alpha30Quality(PortfolioStrategy):
    name = "alpha30_quality"

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
