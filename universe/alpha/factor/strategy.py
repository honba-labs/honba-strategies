"""Strategy: alpha30_factor

Refactored to inherit the shared lifecycle (on_start / on_bar / helpers)
from AlphaBase.  The rebalance logic is an equal-weight allocation identical
to alpha30_equal_weight – this strategy is kept as a separate entry-point so
it can carry its own config / backtest artefacts.
"""
from __future__ import annotations

import math
from typing import ClassVar

from honba.strategies.sizing import whole_shares

try:
    from ..base import AlphaBase
except (ImportError, ValueError):
    from universe.alpha.base import AlphaBase



class Alpha30Factor(AlphaBase):
    """Equal-weight α-30 strategy (legacy entry-point).

    All shared mechanics (universe resolution, day-counting, portfolio
    valuation) live in :class:`AlphaBase`; this class only implements
    ``_rebalance``.
    """

    name: ClassVar[str] = "alpha30_factor"

    def _rebalance(self) -> None:
        """Rebalance to equal weight across the current α-30 universe."""
        port_val = self._portfolio_value()
        if port_val <= 0:
            return

        n = len(self._universe)
        if n == 0:
            return

        target_notional = (port_val * self.allocation) / n

        # 1. Exit leavers
        held = {iid for iid, qty in self.ctx.positions().items() if qty > 0}
        for iid in held - self._universe:
            qty = self.position(iid)
            if qty > 0 and not self.busy(iid):
                self.sell(iid, qty)

        # 2. Equalise survivors + enter joiners
        for iid in self._universe:
            if self.busy(iid):
                continue
            px = self._last_prices.get(iid)
            if px is None or px <= 0:
                continue
            target_qty = whole_shares(target_notional, 1.0, px)
            diff = target_qty - self.position(iid)
            if abs(diff) < 1:
                continue
            if diff > 0:
                self.buy(iid, diff)
            else:
                self.sell(iid, -diff)
