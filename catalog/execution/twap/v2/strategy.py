"""TWAP execution strategy v2 (Latest & Recommended)."""

from __future__ import annotations

from typing import Any

from honba_strategies.execution import TwapConfig
from honba_strategies.execution import TwapStrategy as _BaseTwapStrategy


class TwapStrategy(_BaseTwapStrategy):
    """TWAP execution strategy v2 (honba.v2.Strategy contract with event-driven hooks)."""

    name = "twap"
    __strategy_api_version__ = "2.0.0"

    def on_step(self, event: Any, ctx: Any = None) -> None:
        """Called on every market event (Bar, Tick, etc.).

        Dispatches Bar events to `on_bar(bar, ctx)` if defined.
        """
        bar = getattr(event, "bar", None)
        if bar is not None:
            self.on_bar(bar, ctx)
        elif hasattr(event, "close") and hasattr(event, "open"):
            self.on_bar(event, ctx)


__all__ = ["TwapConfig", "TwapStrategy"]
