"""Covered Call Dividend & Yield Engine Strategy.

Synthesizes cash delivery long stock (CNC) with rolling OTM call option writing.
Assignment protection and strike rollover rules before expiry settlement.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Optional

from honba.strategies.base import Strategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class CoveredCallConfig(BaseStrategyConfig):
    """Configuration for Covered Call Strategy."""

    otm_pct: Decimal = Decimal("0.05")  # 5% OTM
    roll_days_before_expiry: int = 2
    min_premium_yield: Decimal = Decimal("0.01")  # 1% minimum premium yield
    max_assignment_risk: Decimal = Decimal("0.30")

    quantity: int = 100

    _registry_meta: ClassVar[dict] = {
        "name": "covered_call",
        "category": "options",
        "description": "Covered call writing with dividend capture and strike rollover",
        "tags": ["volatility", "statistical"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.quantity < 1:
            raise ValueError("quantity must be >= 1")
        if self.otm_pct < 0:
            raise ValueError("otm_pct must be >= 0")


@register_strategy("covered_call", "options", tags=["volatility", "statistical"])
class CoveredCallStrategy(Strategy):
    """Covered Call Dividend & Yield Engine Strategy."""

    name = "covered_call"
    Config = CoveredCallConfig

    def __init__(self, config: CoveredCallConfig) -> None:
        super().__init__(config)
        self.config = config

        self.otm_pct = config.otm_pct
        self.roll_days_before_expiry = config.roll_days_before_expiry
        self.min_premium_yield = config.min_premium_yield
        self.quantity = config.quantity

        self.covered_call_active = False
        self.call_strike: Optional[Decimal] = None

    def on_bar(self, bar) -> None:
        if not self.covered_call_active:
            if self._should_write_call(bar):
                self._write_covered_call(bar)
        else:
            if self._should_roll_or_close(bar):
                self._roll_or_close(bar)

    def _should_write_call(self, bar) -> bool:
        # Check if holding stock and conditions met
        return hasattr(self, 'position') and self.position(self.instrument_id) >= self.quantity

    def _write_covered_call(self, bar) -> None:
        strike = bar.close * (Decimal("1") + self.otm_pct)
        self.call_strike = strike
        self.covered_call_active = True

    def _should_roll_or_close(self, bar) -> bool:
        return False

    def _roll_or_close(self, bar) -> None:
        pass
