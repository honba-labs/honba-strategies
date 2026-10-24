"""POV execution strategy - catalog entry."""

from honba_strategies.execution import PovConfig
from honba_strategies.execution import PovStrategy as _PovStrategy


class PovStrategy(_PovStrategy):
    """POV execution strategy - catalog entry."""
    pass


__all__ = ["PovConfig", "PovStrategy"]
