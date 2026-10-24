"""Equal Weight & Periodic Rebalancer Strategy.

Target weight allocations across universe with configurable drift threshold
bands (e.g. ±5%). Transaction cost aware rebalancing threshold gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Dict, Optional

from honba.strategies.base import Strategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class EqualWeightConfig(BaseStrategyConfig):
    """Configuration for Equal Weight Rebalancing Strategy."""

    # Rebalancing parameters
    rebalance_frequency: str = "daily"  # daily, weekly, monthly
    drift_threshold: Decimal = Decimal("0.05")  # 5% drift threshold
    transaction_cost_bps: Decimal = Decimal("5")  # 5 bps transaction cost
    min_rebalance_value: Decimal = Decimal("10000")  # Minimum value to rebalance

    # Universe parameters
    max_positions: int = 10

    _registry_meta: ClassVar[dict] = {
        "name": "equal_weight",
        "category": "portfolio",
        "description": "Equal weight portfolio with periodic rebalancing and drift threshold bands",
        "tags": ["statistical", "breadth"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.drift_threshold < 0:
            raise ValueError("drift_threshold must be >= 0")
        if self.max_positions < 1:
            raise ValueError("max_positions must be >= 1")


@register_strategy("equal_weight", "portfolio", tags=["statistical", "breadth"])
class EqualWeightRebalancer(Strategy):
    """Equal Weight & Periodic Rebalancer Strategy."""

    name = "equal_weight"
    Config = EqualWeightConfig

    def __init__(self, config: EqualWeightConfig) -> None:
        super().__init__(config)
        self.config = config

        self.drift_threshold = config.drift_threshold
        self.transaction_cost_bps = config.transaction_cost_bps
        self.max_positions = config.max_positions

        self.target_weights: Dict[str, Decimal] = {}
        self.universe: list[str] = []

    def on_start(self) -> None:
        """Initialize equal weights for universe."""
        # In practice, universe comes from filter
        if hasattr(self, 'universe_list') and self.universe_list:
            self.universe = self.universe_list[:self.max_positions]
        else:
            self.universe = []

        if self.universe:
            equal_w = Decimal("1") / Decimal(str(len(self.universe)))
            for symbol in self.universe:
                self.target_weights[symbol] = equal_w

    def on_bar(self, bar) -> None:
        """Check for rebalancing needs."""
        # Check if it's rebalancing time (simplified)
        if not self.target_weights:
            return

        # Calculate current weights and drift
        needs_rebalance = False
        total_value = Decimal("0")
        current_values = {}

        for symbol in self.universe:
            pos = self.position(symbol) if hasattr(self, 'position') else Decimal("0")
            price = bar.close if symbol == self.instrument_id else Decimal("0")
            current_values[symbol] = pos * price
            total_value += current_values[symbol]

        if total_value == 0:
            return

        # Check drift
        for symbol, target_w in self.target_weights.items():
            current_w = current_values.get(symbol, Decimal("0")) / total_value
            drift = abs(current_w - target_w)
            if drift > self.drift_threshold:
                needs_rebalance = True
                break

        if needs_rebalance:
            self._rebalance(current_values, total_value)

    def _rebalance(self, current_values: Dict[str, Decimal], total_value: Decimal) -> None:
        """Perform rebalancing trades."""
        for symbol, target_w in self.target_weights.items():
            target_value = total_value * target_w
            current_value = current_values.get(symbol, Decimal("0"))
            diff_value = target_value - current_value

            # Check transaction cost threshold
            trade_cost = abs(diff_value) * (self.transaction_cost_bps / Decimal("10000"))
            if trade_cost > self.config.min_rebalance_value:
                continue

            if abs(diff_value) < self.config.min_rebalance_value:
                continue

            # Get price (simplified)
            price = Decimal("100")  # Should get from market data
            qty = diff_value / price

            if qty > 0:
                self.buy(symbol, float(qty))
            elif qty < 0:
                self.sell(symbol, float(abs(qty)))
