"""Catalog entry wrapper for ATR Volatility Sizer.

Thin wrapper that imports the sizer from the honba_strategies SDK
for use in declarative step.toml pipelines.
"""

from honba_strategies.components.sizers import AtrVolatilitySizer

# Re-export for catalog discovery
__all__ = ["AtrVolatilitySizer"]

# Catalog metadata
CATALOG_NAME = "atr_volatility"
CATALOG_KIND = "size"
CATALOG_DESCRIPTION = "ATR Volatility Sizing: Inverse volatility allocation based on Average True Range with optional portfolio volatility targeting"