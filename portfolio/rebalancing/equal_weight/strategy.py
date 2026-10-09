"""Equal-weight periodic rebalance (catalog strategy).

A thin binding of ``PortfolioStrategy`` to ``config.toml``: every ``schedule`` it re-reads the
universe, drops leavers, adds joiners and returns every member to an equal weight. All logic
lives in ``honba.strategies.portfolio``; this class only builds the parts from ``params``.
"""

from __future__ import annotations

from honba.strategies.config import StrategyConfig
from honba.strategies.portfolio.factory import build_portfolio_strategy
from honba.strategies.portfolio.strategy import PortfolioStrategy


class EqualWeightRebalance(PortfolioStrategy):
    name = "equal_weight_rebalance"

    def __init__(self, config: StrategyConfig) -> None:
        params = {"exchange": config.exchange, **config.params}
        parts = build_portfolio_strategy(params, name=self.name)
        super().__init__(
            parts.universe_source,
            parts.weighting,
            parts.schedule,
            parts.selector,
            allocation=parts.allocation,
            name=self.name,
            history_len=parts._history.maxlen,
        )
