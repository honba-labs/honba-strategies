"""Calendar Spread Time-Decay Strategy.

Long far-term option + Short near-term option at same strike.
Profits from time-decay differential (theta) and term structure.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import Strategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class CalendarSpreadConfig(BaseStrategyConfig):
    """Configuration for Calendar Spread Strategy."""

    # Spread parameters
    strike_selection: str = "atm"  # "atm", "otm_call", "otm_put"
    near_expiry_days: int = 7
    far_expiry_days: int = 35
    profit_target_pct: Decimal = Decimal("0.25")
    stop_loss_pct: Decimal = Decimal("0.50")

    # Position sizing
    lots: int = 1

    _registry_meta: ClassVar[dict] = {
        "name": "calendar_spread",
        "category": "options",
        "description": "Time-decay term structure calendar spread",
        "tags": ["volatility", "calendar", "theta"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.lots < 1:
            raise ValueError("lots must be >= 1")
        if self.near_expiry_days >= self.far_expiry_days:
            raise ValueError("near_expiry_days must be < far_expiry_days")
        if self.strike_selection not in ("atm", "otm_call", "otm_put"):
            raise ValueError("strike_selection must be atm, otm_call, or otm_put")


@register_strategy("calendar_spread", "options", tags=["volatility", "calendar", "theta"])
class CalendarSpreadStrategy(Strategy):
    """Time-Decay Term Structure Calendar Spread Strategy.

    Long far-term option + Short near-term option at same strike.
    Profits from theta decay differential and term structure.
    """

    name = "calendar_spread"
    Config = CalendarSpreadConfig

    def __init__(self, config: CalendarSpreadConfig) -> None:
        super().__init__()
        self.config = config

        self.strike_selection = config.strike_selection
        self.near_expiry_days = config.near_expiry_days
        self.far_expiry_days = config.far_expiry_days
        self.profit_target_pct = config.profit_target_pct
        self.stop_loss_pct = config.stop_loss_pct
        self.lots = config.lots

        self.spread_entered = False
        self.entry_debit: Decimal | None = None

    def on_bar(self, bar) -> None:
        """Manage calendar spread position."""
        if not self.spread_entered:
            if self._is_entry_time(bar):
                self._enter_spread(bar)
        else:
            if self._is_exit_time(bar):
                self._exit_spread(bar)
                return

            if self._check_profit_target(bar):
                self._exit_spread(bar)
                return

            if self._check_stop_loss(bar):
                self._exit_spread(bar)

    def _is_entry_time(self, bar) -> bool:
        # Simplified: enter at 09:30
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour >= 9 and bar.ts.minute >= 30
        return False

    def _is_exit_time(self, bar) -> bool:
        # Exit at 15:15
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour >= 15 and bar.ts.minute >= 15
        return False

    def _enter_spread(self, bar) -> None:
        """Enter calendar spread at selected strike."""
        # Simplified - would need option chain data
        spot = bar.close
        if self.strike_selection == "atm":
            strike = spot
        elif self.strike_selection == "otm_call":
            strike = spot * Decimal("1.02")
        else:  # otm_put
            strike = spot * Decimal("0.98")

        # Estimate premiums (simplified)
        near_premium = spot * Decimal("0.015")  # 7-day
        far_premium = spot * Decimal("0.035")   # 35-day
        self.entry_debit = far_premium - near_premium

        self.spread_entered = True
        # Would place: Buy far-term, Sell near-term at same strike

    def _exit_spread(self, bar) -> None:
        """Exit calendar spread."""
        self.spread_entered = False
        self.entry_debit = None

    def _check_profit_target(self, bar) -> bool:
        """Check if profit target reached."""
        if self.entry_debit is None:
            return False
        # Simplified: would calculate current spread value
        return False

    def _check_stop_loss(self, bar) -> bool:
        """Check stop-loss."""
        if self.entry_debit is None:
            return False
        # Stop at 50% of debit
        return False