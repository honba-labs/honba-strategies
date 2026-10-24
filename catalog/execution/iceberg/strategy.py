"""Iceberg execution strategy - catalog entry."""

from honba_strategies.execution import IcebergConfig
from honba_strategies.execution import IcebergStrategy as _IcebergStrategy


class IcebergStrategy(_IcebergStrategy):
    """Iceberg execution strategy - catalog entry."""
    pass


__all__ = ["IcebergConfig", "IcebergStrategy"]
