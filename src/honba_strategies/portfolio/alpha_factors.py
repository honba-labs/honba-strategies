"""Alpha Factor Portfolio Strategy.

Multi-factor portfolio scoring (Momentum, Low Vol, Quality, Value)
across NSE indices (NIFTY 200, NIFTY 500).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Dict, Optional

from honba.strategies.base import Strategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class AlphaFactorConfig(BaseStrategyConfig):
    """Configuration for Alpha Factor Portfolio."""

    # Factor weights
    momentum_weight: Decimal = Decimal("0.25")
    low_vol_weight: Decimal = Decimal("0.25")
    quality_weight: Decimal = Decimal("0.25")
    value_weight: Decimal = Decimal("0.25")

    lookback_window: int = 252
    rebalance_frequency: str = "monthly"
    top_n: int = 30  # Number of stocks to hold
    max_weight: Decimal = Decimal("0.10")

    _registry_meta: ClassVar[dict] = {
        "name": "alpha30_factor",
        "category": "portfolio",
        "description": "Multi-factor portfolio (Momentum, Low Vol, Quality, Value) selecting top N stocks",
        "tags": ["momentum", "statistical", "breadth"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        total_w = self.momentum_weight + self.low_vol_weight + self.quality_weight + self.value_weight
        if abs(total_w - Decimal("1")) > Decimal("0.01"):
            raise ValueError("Factor weights must sum to 1.0")
        if self.top_n < 1:
            raise ValueError("top_n must be >= 1")


@register_strategy("alpha30_factor", "portfolio", tags=["momentum", "statistical", "breadth"])
class AlphaFactorStrategy(Strategy):
    """Alpha Factor Portfolio Strategy."""

    name = "alpha30_factor"
    Config = AlphaFactorConfig

    def __init__(self, config: AlphaFactorConfig) -> None:
        super().__init__(config)
        self.config = config

        self.momentum_weight = config.momentum_weight
        self.low_vol_weight = config.low_vol_weight
        self.quality_weight = config.quality_weight
        self.value_weight = config.value_weight
        self.top_n = config.top_n
        self.max_weight = config.max_weight

        self.factor_scores: Dict[str, Decimal] = {}
        self.target_weights: Dict[str, Decimal] = {}
        self.universe: list[str] = []

    def on_start(self) -> None:
        if hasattr(self, 'universe_list') and self.universe_list:
            self.universe = self.universe_list
        else:
            self.universe = []

    def on_bar(self, bar) -> None:
        if not self.universe:
            return
        # Calculate factor scores and rebalance
        self._calculate_factor_scores()
        self._construct_portfolio()

    def _calculate_factor_scores(self) -> None:
        """Calculate multi-factor scores."""
        for symbol in self.universe:
            # Simplified factor scores
            momentum_score = Decimal("0.5")  # Placeholder
            low_vol_score = Decimal("0.5")
            quality_score = Decimal("0.5")
            value_score = Decimal("0.5")

            composite = (
                self.momentum_weight * momentum_score +
                self.low_vol_weight * low_vol_score +
                self.quality_weight * quality_score +
                self.value_weight * value_score
            )
            self.factor_scores[symbol] = composite

    def _construct_portfolio(self) -> None:
        """Construct portfolio from top N stocks."""
        if not self.factor_scores:
            return

        # Sort by composite score
        sorted_stocks = sorted(
            self.factor_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        top_stocks = sorted_stocks[:self.top_n]
        n = len(top_stocks)
        equal_w = Decimal("1") / Decimal(str(n))

        self.target_weights = {}
        for symbol, _ in top_stocks:
            w = equal_w
            if w > self.max_weight:
                w = self.max_weight
            self.target_weights[symbol] = w

        # Normalize
        total_w = sum(self.target_weights.values())
        if total_w > 0:
            for symbol in self.target_weights:
                self.target_weights[symbol] = self.target_weights[symbol] / total_w
