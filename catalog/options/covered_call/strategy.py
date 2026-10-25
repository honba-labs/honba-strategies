"""Catalog entry wrapper for Covered Call Strategy.

Thin wrapper that imports the strategy from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.options import CoveredCallConfig, CoveredCallStrategy

# Re-export for catalog discovery
__all__ = ["CoveredCallConfig", "CoveredCallStrategy"]

# Catalog metadata
CATALOG_NAME = "covered_call"
CATALOG_KIND = "signal"
CATALOG_DESCRIPTION = "Covered call writing with dividend capture and strike rollover on CNC delivery stocks"