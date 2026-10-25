"""Catalog entry wrapper for Fixed Fractional Sizer.

Thin wrapper that imports the sizer from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.components.sizers import FixedFractionalSizer

# Re-export for catalog discovery
__all__ = ["FixedFractionalSizer"]

# Catalog metadata
CATALOG_NAME = "fixed_fractional"
CATALOG_KIND = "size"
CATALOG_DESCRIPTION = "Fixed Fractional Sizing: Risk a fixed percentage of equity per trade vs stop-loss distance"