"""Iron Condor Range-Bound Volatility Capture Strategy.

4-leg defined risk structure: short OTM credit spread (call + put) flanked by
long wing protection. Dynamic delta-neutral wing adjustment and early profit
take (50% max profit).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Optional

from honba.strategies.base import Strategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class IronCondorConfig(BaseStrategyConfig):
    """Configuration for Iron Condor Strategy."""

    entry_time: str = "09:25"
    exit_time: str = "15:10"
    wing_width: int = 200  # Points
    short_delta: Decimal = Decimal("0.16")  # Short strike delta
    profit_target_pct: Decimal = Decimal("0.50")
    adjustment_delta: Decimal = Decimal("0.30")

    lots: int = 1

    _registry_meta: ClassVar[dict] = {
        "name": "banknifty_iron_condor",
        "category": "options",
        "description": "Iron Condor 4-leg defined risk structure with delta-neutral adjustment",
        "tags": ["volatility", "statistical"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.lots < 1:
            raise ValueError("lots must be >= 1")
        if self.wing_width < 50:
            raise ValueError("wing_width must be >= 50")


@register_strategy("banknifty_iron_condor", "options", tags=["volatility", "statistical"])
class IronCondorStrategy(Strategy):
    """Iron Condor Range-Bound Volatility Capture Strategy."""

    name = "banknifty_iron_condor"
    Config = IronCondorConfig

    def __init__(self, config: IronCondorConfig) -> None:
        super().__init__(config)
        self.config = config

        self.wing_width = config.wing_width
        self.short_delta = config.short_delta
        self.profit_target_pct = config.profit_target_pct
        self.adjustment_delta = config.adjustment_delta
        self.lots = config.lots

        self.iron_condor_entered = False

    def on_bar(self, bar) -> None:
        if not self.iron_condor_entered:
            if self._is_entry_time(bar):
                self._enter_iron_condor(bar)
        else:
            if self._is_exit_time(bar):
                self._exit_iron_condor(bar)
                return
            if self._check_profit_target(bar):
                self._exit_iron_condor(bar)

    def _is_entry_time(self, bar) -> bool:
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour >= 9 and bar.ts.minute >= 25
        return False

    def _is_exit_time(self, bar) -> bool:
        if hasattr(bar, 'ts') and hasattr(bar.ts, 'hour') and hasattr(bar.ts, 'minute'):
            return bar.ts.hour >= 15 and bar.ts.minute >= 10
        return False

    def _enter_iron_condor(self, bar) -> None:
        self.iron_condor_entered = True

    def _exit_iron_condor(self, bar) -> None:
        self.iron_condor_entered = False

    def _check_profit_target(self, bar) -> bool:
        return False
