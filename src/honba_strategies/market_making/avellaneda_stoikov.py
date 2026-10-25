"""Avellaneda-Stoikov Market Maker.

Dynamic reservation price calculation based on inventory risk aversion parameter γ:
R(s, q, t) = s - q * γ * σ² * (T - t)

Asymmetric quoting skew: lowers bid and widens ask when inventory is long;
raises bid when short. Dynamic half-spread calculation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import QuotingStrategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class AvellanedaStoikovConfig(BaseStrategyConfig):
    """Configuration for Avellaneda-Stoikov Market Maker."""

    # Model parameters
    gamma: Decimal = Decimal("0.1")  # Risk aversion parameter
    sigma: Decimal = Decimal("0.02")  # Volatility estimate (daily)
    kappa: Decimal = Decimal("1.5")  # Arrival rate sensitivity

    # Time parameters
    time_horizon_days: int = 1  # Trading horizon (T)
    current_time_days: Decimal = Decimal("0")  # Current time (t)

    # Execution parameters
    quote_quantity: Decimal = Decimal("100")  # Base quote size
    max_inventory: Decimal = Decimal("1000")  # Max net position
    skew_scale: Decimal = Decimal("1.0")  # Inventory skew scaling

    # Risk parameters
    max_position_pct: Decimal = Decimal("0.05")
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "avellaneda_stoikov",
        "category": "market_making",
        "description": "Avellaenda-Stoikov inventory-aware market making with dynamic skew",
        "tags": ["market_making", "avellaneda_stoikov", "inventory"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.gamma <= 0:
            raise ValueError("gamma must be positive")
        if self.sigma <= 0:
            raise ValueError("sigma must be positive")
        if self.kappa <= 0:
            raise ValueError("kappa must be positive")


@register_strategy("avellaneda_stoikov", "market_making", tags=["market_making", "avellaneda_stoikov", "inventory"])
class AvellanedaStoikovStrategy(QuotingStrategy):
    """Avellaneda-Stoikov inventory-aware market maker."""

    name = "avellaneda_stoikov"
    Config = AvellanedaStoikovConfig

    def __init__(self, config: AvellanedaStoikovConfig) -> None:
        super().__init__(
            quoting_side="BOTH",
            quoting_quantity=config.quote_quantity,
            price_tolerance=Decimal("0.1"),
        )
        self.config = config
        self.gamma = float(config.gamma)
        self.sigma = float(config.sigma)
        self.kappa = float(config.kappa)
        self.T = float(config.time_horizon_days)
        self.t = float(config.current_time_days)
        self.max_inventory = config.max_inventory
        self.quote_quantity = config.quote_quantity
        self.skew_scale = float(config.skew_scale)

    def on_start(self) -> None:
        """Initialize time tracking."""
        self.t = float(self.config.current_time_days)

    def on_quote(self, quote) -> None:
        """Update quotes based on Avellaneda-Stoikov model."""
        mid = (quote.bid_price + quote.ask_price) / 2
        current_pos = self.ctx.position(self.instrument_id) if hasattr(self, 'instrument_id') else Decimal("0")
        q = float(current_pos)

        # Time remaining
        tau = max(self.T - self.t, 0.001)

        # Reservation price: R = s - q * γ * σ² * (T - t)
        reservation_price = float(mid) - q * self.gamma * (self.sigma ** 2) * tau

        # Optimal half-spread: δ = (1/γ) * ln(1 + γ/κ) + 0.5 * γ * σ² * (T - t)
        half_spread = (1.0 / self.gamma) * math.log(1.0 + self.gamma / self.kappa) + \
                      0.5 * self.gamma * (self.sigma ** 2) * tau

        # Inventory skew: adjust prices based on inventory
        skew = q * self.gamma * (self.sigma ** 2) * tau * float(self.config.skew_scale)

        # Final bid/ask prices
        bid_price = Decimal(str(reservation_price - half_spread - skew))
        ask_price = Decimal(str(reservation_price + half_spread - skew))

        # Inventory limits
        if float(current_pos) >= float(self.max_inventory):
            ask_price = None  # Don't sell more
        elif float(current_pos) <= -float(self.max_inventory):
            bid_price = None  # Don't buy more

        # Update quotes
        if bid_price is not None:
            self.update_quote(
                instrument_id=self.instrument_id,
                target_price=bid_price,
                target_qty=self.config.quote_quantity,
            )
        if ask_price is not None:
            self.update_quote(
                instrument_id=self.instrument_id,
                target_price=ask_price,
                target_qty=self.config.quote_quantity,
            )

    def on_fill(self, fill) -> None:
        """Update inventory tracking."""
        super().on_fill(fill)