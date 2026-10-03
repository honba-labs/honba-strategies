"""Alpha-30 equal-weight rebalancer (catalog strategy).

Universe  : Nifty200 Alpha 30  (resolved via honba.markets.india.universes)
Allocation: equal capital across every current member
Rebalance : every `rebalance_days` trading days

On each rebalance:
  1. Sell names that left the index
  2. Buy names that joined the index
  3. Trim overweight / top-up underweight so every survivor is equal-weight again

Membership is always obtained through the engine API
(resolve_universe).  A seed list is used only when the engine does not
yet know the universe name (learning / CI environments).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from honba.domain.bar import Bar
from honba.domain.instrument import InstrumentId
from honba.markets.india.universes import resolve_universe, UNIVERSES
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.sizing import whole_shares

# ---------------------------------------------------------------------------
# Seed (used only when the engine has not registered the universe yet)
# ---------------------------------------------------------------------------
_SEED: tuple[str, ...] = (
    "ADANIPOWER", "SHRIRAMFIN", "HINDALCO", "ADANIGREEN", "EICHERMOT",
    "ADANIENSOL", "IDEA", "BHEL", "CUMMINSIND", "POWERINDIA",
    "POLYCAB", "MUTHOOTFIN", "PAYTM", "INDIANB", "LAURUSLABS",
    "VEDL", "BHARATFORG", "NYKAA", "ASHOKLEY", "MCX",
    "FEDERALBNK", "AUBANK", "LTF", "SAIL", "GLENMARK",
    "FORTIS", "NATIONALUM", "BSE", "ABCAPITAL", "DIXON",
)

UNIVERSE_KEY = "nifty200_alpha_30"


def _ensure_registered() -> None:
    """Idempotently inject the seed so resolve_universe never fails in CI."""
    if UNIVERSE_KEY not in UNIVERSES:
        UNIVERSES[UNIVERSE_KEY] = _SEED


def _resolve(venue: str = "NSE") -> set[InstrumentId]:
    _ensure_registered()
    return set(resolve_universe(UNIVERSE_KEY, venue=venue))


class Alpha30EqualWeight(Strategy):
    name = "alpha30_equal_weight"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.capital: float = float(p.get("capital", 1_000_000))
        self.allocation: float = float(p.get("allocation", 0.98))
        self.rebalance_days: int = int(p.get("rebalance_days", 15))
        self.venue: str = config.venue or "NSE"

        self._universe: set[InstrumentId] = set()
        self._last_prices: dict[InstrumentId, float] = {}
        self._last_day: date | None = None
        self._days_since: int = 0
        self._initial_done: bool = False

    # ------------------------------------------------------------------
    def on_start(self) -> None:
        self._universe = _resolve(self.venue)

    def on_bar(self, bar: Bar) -> None:
        self._last_prices[bar.instrument_id] = float(bar.close)

        day = _bar_day(bar, self.ctx.now())
        day_changed = False
        if self._last_day is None:
            self._last_day = day
        elif day > self._last_day:
            self._days_since += 1
            self._last_day = day
            day_changed = True

        if not self._initial_done:
            # Rebalance on the initial day once prices are known for all members,
            # or on day rollover as a fallback.
            if len(self._last_prices) >= len(self._universe) or day_changed:
                self._rebalance()
                self._initial_done = True
                self._days_since = 0
            return

        if self._days_since >= self.rebalance_days:
            self._rebalance()
            self._days_since = 0

    def _portfolio_value(self) -> float:
        """Cash + mark-to-market of every open position."""
        value = float(self.ctx.cash())
        for iid, qty in self.ctx.positions().items():
            if qty == 0:
                continue
            px = self._last_prices.get(iid)
            if px is not None and px > 0:
                value += qty * px
        return value


    def _rebalance(self) -> None:
        previous = set(self._universe)
        self._universe = _resolve(self.venue)
        if not self._universe:
            return

        # Log membership changes
        joined = self._universe - previous
        left = previous - self._universe
        if joined:
            self.log_event("EVENT_MEMBERSHIP_ADD", symbols=[i.symbol for i in sorted(joined, key=lambda x: x.symbol)])
        if left:
            self.log_event("EVENT_MEMBERSHIP_DEL", symbols=[i.symbol for i in sorted(left, key=lambda x: x.symbol)])

        # ----- FIX: size off live equity, not the original capital -----
        port_val = self._portfolio_value()
        if port_val <= 0:
            return

        n = len(self._universe)
        target_notional = (port_val * self.allocation) / n
        # ---------------------------------------------------------------

        # 1. Exit leavers
        held = {iid for iid, qty in self.ctx.positions().items() if qty > 0}
        for iid in held - self._universe:
            qty = self.position(iid)
            if qty > 0 and not self.busy(iid):
                self.sell(iid, qty, reason="exit")

        # 2 + 3. Enter joiners & equalise survivors
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
                self.sell(iid, -diff, reason="rebalance")


def _bar_day(bar: Bar, now_ns: int) -> date:
    ts: Any = getattr(bar, "ts", None) or getattr(bar, "ts_event", None)
    if ts is not None and hasattr(ts, "date"):
        return ts.date()
    if isinstance(ts, (int, float)):
        v = float(ts)
        if v > 1e13:
            v /= 1e9
        elif v > 1e11:
            v /= 1e3
        return datetime.fromtimestamp(v, tz=timezone.utc).date()
    if now_ns > 0:
        return datetime.fromtimestamp(now_ns / 1e9, tz=timezone.utc).date()
    return date.today()