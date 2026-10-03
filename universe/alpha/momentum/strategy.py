"""Strategy: alpha30_momentum

Selects the `top_n` best-performing constituents of the α-30 universe over a
trailing `mom_window` trading-day window and holds them equal-weighted.

Standard academic momentum skips the most-recent month to avoid short-term
reversal; this implementation uses a configurable `skip_days` parameter
(default 5 trading days) for the same purpose.

Configuration params (all optional):
  capital         = 1_000_000
  allocation      = 0.98
  rebalance_days  = 15
  mom_window      = 60          # lookback for return calculation (trading days)
  skip_days       = 5           # recent days to skip (short-term reversal filter)
  top_n           = 10          # number of top-momentum names to hold
"""
from __future__ import annotations

import math
from typing import ClassVar

from honba.domain.instrument import InstrumentId
from honba.strategies.sizing import whole_shares

try:
    from ..base import AlphaBase
except (ImportError, ValueError):
    from universe.alpha.base import AlphaBase



class Alpha30Momentum(AlphaBase):
    """Equal-weight portfolio of the highest-momentum α-30 constituents.

    Signal: total return over [-(mom_window + skip_days), -skip_days] days.
    All shared mechanics live in :class:`AlphaBase`; this class maintains a
    price-history buffer and implements ``_rebalance``.
    """

    name: ClassVar[str] = "alpha30_momentum"
    DEFAULT_REBALANCE_DAYS: ClassVar[int] = 15

    def __init__(self, config) -> None:  # type: ignore[override]
        super().__init__(config)
        p = config.params
        self._mom_window: int = int(p.get("mom_window", 60))
        self._skip_days: int = int(p.get("skip_days", 5))
        self._top_n: int = int(p.get("top_n", 10))
        # keep enough history for window + skip
        self._buf: int = self._mom_window + self._skip_days + 1
        self._price_history: dict[InstrumentId, list[float]] = {}

    def on_bar(self, bar) -> None:  # type: ignore[override]
        iid = bar.instrument_id
        hist = self._price_history.setdefault(iid, [])
        hist.append(float(bar.close))
        if len(hist) > self._buf:
            hist.pop(0)
        super().on_bar(bar)

    # ------------------------------------------------------------------
    def _momentum(self, iid: InstrumentId) -> float:
        """Trailing return excluding the most-recent `skip_days`; -inf if unknown."""
        hist = self._price_history.get(iid, [])
        needed = self._skip_days + 2          # at least start + end price
        if len(hist) < needed:
            return float("-inf")
        end_idx = len(hist) - 1 - self._skip_days
        start_idx = max(0, end_idx - self._mom_window)
        p_start = hist[start_idx]
        p_end = hist[end_idx]
        if p_start <= 0:
            return float("-inf")
        return (p_end - p_start) / p_start

    def _rebalance(self) -> None:
        """Hold the `top_n` highest-momentum names, equal-weighted."""
        port_val = self._portfolio_value()
        if port_val <= 0:
            return

        # Rank descending by momentum signal.
        ranked = sorted(self._universe, key=self._momentum, reverse=True)
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
