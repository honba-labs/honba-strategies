"""Options & Volatility Trading Strategies.

All options strategies handle multi-leg positions, Greeks management,
margin awareness, and use exact Decimal arithmetic.
"""

from honba_strategies.options.calendar_spread import CalendarSpreadConfig, CalendarSpreadStrategy
from honba_strategies.options.covered_call import CoveredCallConfig, CoveredCallStrategy
from honba_strategies.options.iron_condor import IronCondorConfig, IronCondorStrategy
from honba_strategies.options.straddle import ShortStraddleConfig, ShortStraddleStrategy

__all__ = [
    "CalendarSpreadConfig",
    "CalendarSpreadStrategy",
    "CoveredCallConfig",
    "CoveredCallStrategy",
    "IronCondorConfig",
    "IronCondorStrategy",
    "ShortStraddleConfig",
    "ShortStraddleStrategy",
]