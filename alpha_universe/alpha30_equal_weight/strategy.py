"""Equal-weight Nifty200 Alpha 30 rebalancer.

Membership comes exclusively from
``honba.markets.india.universes.resolve_universe`` — never a hardcoded list.
Re-fetched on every rebalance so joiners / leavers are applied.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.markets.india.universes import resolve_universe
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.sizing import whole_shares


class Alpha30EqualWeight(Strategy):
    name = "alpha30_equal_weight"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.capital = float(p.get("capital", 1_000_000))
        self.allocation = float(p.get("allocation", 0.98))
        self.rebalance_days = int(p.get("rebalance_days", 15))
        self.venue = str(p.get("venue", "NSE"))
        # canonical key understood by resolve_universe
        self.universe_name = str(p.get("universe", "nifty200_alpha_30"))

        self._universe: set[InstrumentId] = set()
        self._last_prices: dict[InstrumentId, float] = {}
        self._last_day: date | None = None
        self._days_since_rebalance = 0
        self._initial_done = False

    def on_start(self) -> None:
        self._universe = self._fetch_universe()

    def on_bar(self, bar: Bar) -> None:
        self._last_prices[bar.instrument_id] = float(bar.close)

        day = _bar_day(bar)
        if self._last_day is None:
            self._last_day = day
        if day > self._last_day:
            self._days_since_rebalance += 1
            self._last_day = day

        if not self._initial_done:
            self._rebalance()
            self._initial_done = True
            self._days_since_rebalance = 0
            return

        if self._days_since_rebalance >= self.rebalance_days:
            self._rebalance()
            self._days_since_rebalance = 0

    def _fetch_universe(self) -> set[InstrumentId]:
        """Honba engine API — single source of membership."""
        return set(resolve_universe(self.universe_name, venue=self.venue))

    def _rebalance(self) -> None:
        previous = set(self._universe)
        self._universe = self._fetch_universe()  # re-resolve every time
        if not self._universe:
            return

        n = len(self._universe)
        target_notional = (self.capital * self.allocation) / n
        held = {
            iid for iid, qty in self.ctx.positions().items() if qty > 0
        }

        # exit leavers
        for iid in held - self._universe:
            qty = self.position(iid)
            if qty > 0 and not self.busy(iid):
                self.sell(iid, qty)

        # equal-weight current members (trim winners, top up laggards, enter joiners)
        for iid in self._universe:
            if self.busy(iid):
                continue
            px = self._last_prices.get(iid)
            if px is None or px <= 0:
                continue
            target_qty = whole_shares(target_notional, 1.0, px)
            held_qty = self.position(iid)
            diff = target_qty - held_qty
            if abs(diff) < 1:
                continue
            if diff > 0:
                self.buy(iid, diff)
            else:
                self.sell(iid, -diff)


def _bar_day(bar: Bar) -> date:
    ts: Any = getattr(bar, "ts", None) or getattr(bar, "ts_event", None)
    if ts is None:
        # StrategyContext.now() is unix ns
        return date.today()
    if hasattr(ts, "date"):
        return ts.date()
    if isinstance(ts, (int, float)):
        if ts > 1e14:
            ts = ts / 1e9
        elif ts > 1e11:
            ts = ts / 1e3
        return datetime.fromtimestamp(ts, tz=timezone.utc).date()
    return date.today()