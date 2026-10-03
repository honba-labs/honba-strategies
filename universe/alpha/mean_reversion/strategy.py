"""Strategy: alpha30_mean_reversion

Buys the most-oversold constituents of the α-30 universe and sells the
most-overbought, rebalancing at each cadence.

Ranking signal: z-score of the current price relative to a rolling mean and
std-dev computed over the last `mr_window` trading-day closes.  A lower
z-score means the price is further below its rolling mean (more oversold).
The strategy selects the `top_n` lowest z-score names, holds them
equal-weighted, and exits all others.

Configuration params (all optional):
  capital         = 1_000_000
  allocation      = 0.98
  rebalance_days  = 5           # mean-reversion trades more frequently
  mr_window       = 20          # lookback for rolling mean / std (trading days)
  top_n           = 10          # number of oversold names to hold
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
    from universe.alpha.base import AlphaBase



class Alpha30MeanReversion(AlphaBase):
    """Equal-weight portfolio of the most-oversold α-30 constituents.

    Signal: rolling z-score of close price.  All shared mechanics live in
    :class:`AlphaBase`; this class maintains a price-history buffer and
    implements ``_rebalance``.
    """

    name: ClassVar[str] = "alpha30_mean_reversion"
    DEFAULT_REBALANCE_DAYS: ClassVar[int] = 5

    def __init__(self, config) -> None:  # type: ignore[override]
        super().__init__(config)
        p = config.params
        self._mr_window: int = int(p.get("mr_window", 20))
        self._top_n: int = int(p.get("top_n", 10))
        self._price_history: dict[InstrumentId, list[float]] = {}

    def on_bar(self, bar) -> None:  # type: ignore[override]
        iid = bar.instrument_id
        hist = self._price_history.setdefault(iid, [])
        hist.append(float(bar.close))
        if len(hist) > self._mr_window:
            hist.pop(0)
        super().on_bar(bar)

    # ------------------------------------------------------------------
    def _zscore(self, iid: InstrumentId) -> float:
        """Rolling z-score of the latest price; returns +inf if undetermined."""
        hist = self._price_history.get(iid, [])
        if len(hist) < 2:
            return float("inf")
        try:
            mu = statistics.mean(hist)
            sigma = statistics.stdev(hist)
        except statistics.StatisticsError:
            return float("inf")
        if sigma == 0:
            return 0.0
        return (hist[-1] - mu) / sigma

    def _rebalance(self) -> None:
        """Hold the `top_n` most-oversold names (lowest z-score), equal-weighted."""
        port_val = self._portfolio_value()
        if port_val <= 0:
            return

        # Rank by z-score ascending (most oversold first).
        ranked = sorted(self._universe, key=self._zscore)
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
