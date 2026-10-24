"""TWAP execution strategy - catalog entry."""

from honba_strategies.execution import TwapConfig
from honba_strategies.execution import TwapStrategy as _TwapStrategy


class TwapStrategy(_TwapStrategy):
    """TWAP execution strategy - catalog entry."""
    pass


__all__ = ["TwapConfig", "TwapStrategy"]
