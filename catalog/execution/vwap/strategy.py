"""VWAP execution strategy - catalog entry."""

from honba_strategies.execution import VwapConfig
from honba_strategies.execution import VwapStrategy as _VwapStrategy


class VwapStrategy(_VwapStrategy):
    """VWAP execution strategy - catalog entry."""
    pass


__all__ = ["VwapConfig", "VwapStrategy"]
