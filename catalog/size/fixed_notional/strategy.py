"""Catalog entry wrapper for Fixed Notional Sizer.

Thin wrapper that imports the sizer from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.components.sizers import FixedNotionalSizer

# Re-export for catalog discovery
__all__ = ["FixedNotionalSizer"]

# Catalog metadata
CATALOG_NAME = "fixed_notional"
CATALOG_KIND = "size"
CATALOG_DESCRIPTION = "Fixed Notional Sizing: Targets a fixed cash allocation per position with lot-size discretization"