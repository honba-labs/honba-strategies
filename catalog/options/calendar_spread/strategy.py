"""Catalog entry wrapper for Calendar Spread Strategy.

Thin wrapper that imports the strategy from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.options import CalendarSpreadConfig, CalendarSpreadStrategy

# Re-export for catalog discovery
__all__ = ["CalendarSpreadConfig", "CalendarSpreadStrategy"]

# Catalog metadata
CATALOG_NAME = "calendar_spread"
CATALOG_KIND = "signal"
CATALOG_DESCRIPTION = "Time-decay term structure calendar spread: long far-term option, short near-term option at same strike"