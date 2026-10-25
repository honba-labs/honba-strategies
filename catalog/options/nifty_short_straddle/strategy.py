"""Catalog entry wrapper for NIFTY Short Straddle Strategy.

Thin wrapper that imports the strategy from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.options import ShortStraddleConfig, ShortStraddleStrategy

# Re-export for catalog discovery
__all__ = ["ShortStraddleConfig", "ShortStraddleStrategy"]

# Catalog metadata
CATALOG_NAME = "nifty_short_straddle"
CATALOG_KIND = "signal"
CATALOG_DESCRIPTION = "ATM Short Straddle with dynamic hedging on NIFTY/BANKNIFTY indices"