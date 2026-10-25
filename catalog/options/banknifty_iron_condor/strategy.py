"""Catalog entry wrapper for BankNifty Iron Condor Strategy.

Thin wrapper that imports the strategy from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.options import IronCondorConfig, IronCondorStrategy

# Re-export for catalog discovery
__all__ = ["IronCondorConfig", "IronCondorStrategy"]

# Catalog metadata
CATALOG_NAME = "banknifty_iron_condor"
CATALOG_KIND = "signal"
CATALOG_DESCRIPTION = "Iron Condor 4-leg defined risk structure with delta-neutral adjustment and early profit take"