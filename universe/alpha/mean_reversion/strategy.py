"""Strategy: alpha30_mean_reversion

Selects the 10 most-oversold constituents (lowest price z-score) and holds them equal-weighted.
"""

from __future__ import annotations

from honba.strategies.config import StrategyConfig
from honba.strategies.portfolio.factory import build_portfolio_strategy
from honba.strategies.portfolio.strategy import PortfolioStrategy


class Alpha30MeanReversion(PortfolioStrategy):
    name = "alpha30_mean_reversion"

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
