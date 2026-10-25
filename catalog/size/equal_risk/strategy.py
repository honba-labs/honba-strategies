"""Catalog entry wrapper for Equal Risk Sizer.

Thin wrapper that imports the sizer from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.components.sizers import EqualRiskSizer

# Re-export for catalog discovery
__all__ = ["EqualRiskSizer"]

# Catalog metadata
CATALOG_NAME = "equal_risk"
CATALOG_KIND = "size"
CATALOG_DESCRIPTION = "Equal Risk Contribution Sizing: Allocates risk budget equally across active signals with optional correlation adjustment"