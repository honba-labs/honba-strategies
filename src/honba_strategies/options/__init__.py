"""Options & Volatility Trading Strategies.

All options strategies handle multi-leg positions, Greeks management,
margin awareness, and use exact Decimal arithmetic.
"""

from honba_strategies.options.straddle import ShortStraddleStrategy, ShortStraddleConfig
from honba_strategies.options.iron_condor import IronCondorStrategy, IronCondorConfig
from honba_strategies.options.covered_call import CoveredCallStrategy, CoveredCallConfig

__all__ = [
    "ShortStraddleStrategy",
    "ShortStraddleConfig",
    "IronCondorStrategy",
    "IronCondorConfig",
    "CoveredCallStrategy",
    "CoveredCallConfig",
]
