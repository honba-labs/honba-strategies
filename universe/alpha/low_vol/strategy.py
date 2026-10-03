"""Strategy: alpha30_low_vol

Selects the `top_n` lowest-volatility constituents from the α-30 universe
and holds them in equal weight.  Volatility is estimated as the rolling
standard deviation of daily log-returns over the last `vol_window` days
using only the prices seen so far by the strategy.

Configuration params (all optional):
  capital         = 1_000_000   # INR
  allocation      = 0.98
  rebalance_days  = 15
  vol_window      = 20          # lookback for vol estimate (trading days)
  top_n           = 15          # number of lowest-vol names to hold
"""
from __future__ import annotations

import math
import statistics
from typing import ClassVar

from honba.domain.instrument import InstrumentId
from honba.strategies.sizing import whole_shares

try:
    from ..base import AlphaBase
except (ImportError, ValueError):
    from base import AlphaBase


class Alpha30LowVol(AlphaBase):
    """Equal-weight portfolio of the lowest-volatility α-30 constituents.

    All shared mechanics live in :class:`AlphaBase`; this class adds a
    rolling price history buffer and implements ``_rebalance`` using a
    volatility ranking.
    """

    name: ClassVar[str] = "alpha30_low_vol"
    DEFAULT_REBALANCE_DAYS: ClassVar[int] = 15

    def __init__(self, config) -> None:  # type: ignore[override]
        super().__init__(config)
        p = config.params
        self._vol_window: int = int(p.get("vol_window", 20))
        self._top_n: int = int(p.get("top_n", 15))
        # price_history[iid] = list of recent close prices (newest appended last)
        self._price_history: dict[InstrumentId, list[float]] = {}

    def on_bar(self, bar) -> None:  # type: ignore[override]
        # Maintain rolling price history in addition to base-class bookkeeping.
        iid = bar.instrument_id
        hist = self._price_history.setdefault(iid, [])
        hist.append(float(bar.close))
        if len(hist) > self._vol_window + 1:
            hist.pop(0)
        super().on_bar(bar)

    # ------------------------------------------------------------------
    def _vol(self, iid: InstrumentId) -> float:
        """Rolling annualised log-return std-dev for *iid*, or +inf if unknown."""
        hist = self._price_history.get(iid, [])
        if len(hist) < 2:
            return float("inf")
        log_rets = [
            math.log(hist[i] / hist[i - 1])
            for i in range(1, len(hist))
            if hist[i - 1] > 0 and hist[i] > 0
        ]
        if len(log_rets) < 2:
            return float("inf")
        return statistics.stdev(log_rets) * math.sqrt(252)

    def _rebalance(self) -> None:
        """Hold the `top_n` lowest-volatility names, equal-weighted."""
        port_val = self._portfolio_value()
        if port_val <= 0:
            return

        # Rank constituents by volatility; pick the quietest `top_n`.
        ranked = sorted(self._universe, key=self._vol)
        selected = set(ranked[: self._top_n])
        if not selected:
            return

        n = len(selected)
        target_notional = (port_val * self.allocation) / n

        # 1. Exit positions not in the selected set.
        held = {iid for iid, qty in self.ctx.positions().items() if qty > 0}
        for iid in held - selected:
            qty = self.position(iid)
            if qty > 0 and not self.busy(iid):
                self.sell(iid, qty)

        # 2. Equalise / enter selected positions.
        for iid in selected:
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
