"""TWAP execution strategy v1 (Preserved for existing software)."""

from __future__ import annotations

from honba_strategies.execution import TwapConfig
from honba_strategies.execution import TwapStrategy as _BaseTwapStrategy


class TwapStrategy(_BaseTwapStrategy):
    """TWAP execution strategy v1 (honba.v1.Strategy contract)."""

    name = "twap"
    __strategy_api_version__ = "1.0.0"


__all__ = ["TwapConfig", "TwapStrategy"]
