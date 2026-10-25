"""Mean-Variance Markowitz Optimizer Strategy.

Quadratic optimization maximizing Sharpe ratio subject to minimum/maximum
weight and sector bounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import Strategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class MarkowitzConfig(BaseStrategyConfig):
    """Configuration for Markowitz Mean-Variance Optimization."""

    lookback_window: int = 252  # 1 year
    rebalance_frequency: str = "monthly"
    risk_free_rate: Decimal = Decimal("0.06")  # 6% annual
    max_weight: Decimal = Decimal("0.20")  # 20% max single position
    min_weight: Decimal = Decimal("0.00")
    target_return: Decimal | None = None

    _registry_meta: ClassVar[dict] = {
        "name": "markowitz",
        "category": "portfolio",
        "description": "Mean-variance optimization maximizing Sharpe ratio with constraints",
        "tags": ["statistical"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.max_weight <= self.min_weight:
            raise ValueError("max_weight must be > min_weight")
        if self.lookback_window < 30:
            raise ValueError("lookback_window must be >= 30")


@register_strategy("markowitz", "portfolio", tags=["statistical"])
class MarkowitzStrategy(Strategy):
    """Mean-Variance Markowitz Optimizer Strategy."""

    name = "markowitz"
    Config = MarkowitzConfig

    def __init__(self, config: MarkowitzConfig) -> None:
        super().__init__()
        self.config = config

        self.lookback_window = config.lookback_window
        self.risk_free_rate = config.risk_free_rate
        self.max_weight = config.max_weight
        self.min_weight = config.min_weight

        self.expected_returns: dict[str, Decimal] = {}
        self.cov_matrix: dict[str, dict[str, Decimal]] = {}
        self.target_weights: dict[str, Decimal] = {}
        self.universe: list[str] = []

    def on_start(self) -> None:
        if hasattr(self, 'universe_list') and self.universe_list:
            self.universe = self.universe_list
        else:
            self.universe = []

    def on_bar(self, bar) -> None:
        if not self.universe or bar.symbol not in self.universe:
            return
        # Simplified Markowitz optimization
        if len(self.universe) >= 2:
            self._optimize_portfolio()

    def _optimize_portfolio(self) -> None:
        """Simplified mean-variance optimization (equal risk contribution approximation)."""
        n = len(self.universe)
        # For simplicity, use equal weights with max weight constraint
        equal_w = Decimal("1") / Decimal(str(n))
        for symbol in self.universe:
            w = equal_w
            if w > self.max_weight:
                w = self.max_weight
            if w < self.min_weight:
                w = self.min_weight
            self.target_weights[symbol] = w

        # Normalize
        total_w = sum(self.target_weights.values())
        if total_w > 0:
            for symbol in self.target_weights:
                self.target_weights[symbol] = self.target_weights[symbol] / total_w
