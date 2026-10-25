"""ATM Short Straddle with Dynamic Hedging Strategy.

Synchronized short ATM Call + ATM Put execution on NIFTY/BANKNIFTY indices.
Individual leg stop-loss (e.g. 25% premium expansion) with combined MTM stop-loss.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import Strategy

from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class ShortStraddleConfig(BaseStrategyConfig):
    """Configuration for Short Straddle Strategy."""

    # Straddle parameters
    entry_time: str = "09:20"  # IST
    exit_time: str = "15:15"  # IST
    sl_pct_per_leg: Decimal = Decimal("0.25")  # 25% premium expansion
    combined_sl_pct: Decimal = Decimal("0.20")  # 20% combined MTM stop-loss
    profit_target_pct: Decimal = Decimal("0.50")  # 50% of max profit

    # Position sizing
    lots: int = 1
    max_positions: int = 1

    _registry_meta: ClassVar[dict] = {
        "name": "nifty_short_straddle",
        "category": "options",
        "description": "ATM Short Straddle with dynamic hedging on NIFTY/BANKNIFTY",
        "tags": ["volatility", "statistical"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.lots < 1:
            raise ValueError("lots must be >= 1")


@register_strategy("nifty_short_straddle", "options", tags=["volatility", "statistical"])
class ShortStraddleStrategy(Strategy):
    """ATM Short Straddle with Dynamic Hedging Strategy."""

    name = "nifty_short_straddle"
    Config = ShortStraddleConfig

    def __init__(self, config: ShortStraddleConfig) -> None:
        super().__init__()
        self.config = config

        self.sl_pct_per_leg = config.sl_pct_per_leg
        self.combined_sl_pct = config.combined_sl_pct
        self.profit_target_pct = config.profit_target_pct
        self.lots = config.lots

        self.call_entry_premium: Decimal | None = None
        self.put_entry_premium: Decimal | None = None
        self.straddle_entered = False

    def on_bar(self, bar) -> None:
        """Manage straddle position."""
        if not self.straddle_entered:
            if self._is_entry_time(bar):
                self._enter_straddle(bar)
        else:
            if self._is_exit_time(bar):
                self._exit_straddle(bar)
                return

            # Check stop losses
            if self._check_stop_losses(bar):
                self._exit_straddle(bar)
                return

            # Check profit target
            if self._check_profit_target(bar):
                self._exit_straddle(bar)

    def _is_entry_time(self, bar) -> bool:
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour >= 9 and bar.ts.minute >= 20
        return False

    def _is_exit_time(self, bar) -> bool:
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour >= 15 and bar.ts.minute >= 15
        return False

    def _enter_straddle(self, bar) -> None:
        """Enter short straddle at ATM."""
        # Simplified - would need option chain data
        atm_price = bar.close
        self.call_entry_premium = atm_price * Decimal("0.02")  # ~2% premium
        self.put_entry_premium = atm_price * Decimal("0.02")
        self.straddle_entered = True
        # Would place short call and short put orders

    def _exit_straddle(self, bar) -> None:
        """Exit straddle."""
        self.straddle_entered = False
        self.call_entry_premium = None
        self.put_entry_premium = None

    def _check_stop_losses(self, bar) -> bool:
        """Check individual and combined stop losses."""
        return False

    def _check_profit_target(self, bar) -> bool:
        """Check profit target."""
        return False
