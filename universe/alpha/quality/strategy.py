"""Strategy: alpha30_quality

Holds the full α-30 universe in equal weight.  The "quality" filter is
applied upstream by the index itself (NIFTY 200 ALPHA 30 selects constituents
on combined alpha/quality screens), so this strategy simply tracks the index
with equal capital allocation and rebalances periodically.

This is the simplest possible baseline — sub-strategies may override
``_rebalance`` to apply additional quality signals (e.g. earnings stability,
ROCE ranking) once those data feeds are available.

Configuration params (all optional):
  capital         = 1_000_000
  allocation      = 0.98
  rebalance_days  = 15
"""
from __future__ import annotations

from typing import ClassVar

from honba.strategies.sizing import whole_shares

try:
    from ..base import AlphaBase
except (ImportError, ValueError):
    from base import AlphaBase


class Alpha30Quality(AlphaBase):
    """Equal-weight α-30 strategy tracking the quality-filtered index.

    All shared mechanics live in :class:`AlphaBase`; this class only
    implements ``_rebalance`` (full-universe equal-weight allocation).
    """

    name: ClassVar[str] = "alpha30_quality"

    def _rebalance(self) -> None:
        """Rebalance to equal weight across the full current α-30 universe."""
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
