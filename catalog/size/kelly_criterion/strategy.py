"""Catalog entry wrapper for Kelly Criterion Sizer.

Thin wrapper that imports the sizer from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.components.sizers import KellySizer

# Re-export for catalog discovery
__all__ = ["KellySizer"]

# Catalog metadata
CATALOG_NAME = "kelly_criterion"
CATALOG_KIND = "size"
CATALOG_DESCRIPTION = "Kelly Criterion Sizing: Optimal capital allocation fraction from win-rate and win/loss ratio with fractional Kelly damping"