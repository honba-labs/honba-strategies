# honba‑strategies/universe/alpha/base.py
"""Common functionality for all α‑30 universe‑based strategies."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, ClassVar, Set

from honba.domain.bar import Bar
from honba.domain.instrument import InstrumentId
from honba.markets.india.universes import resolve_universe, UNIVERSES
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.sizing import whole_shares


class AlphaBase(Strategy):
    """Base class that implements the shared mechanics for α‑30 strategies."""

    # ------------------------------------------------------------------ #
    # Sub‑classes override these constants as needed
    # ------------------------------------------------------------------ #
    UNIVERSE_KEY: ClassVar[str] = "nifty200_alpha_30"
    DEFAULT_CAPITAL: ClassVar[float] = 1_000_000.0
    DEFAULT_ALLOCATION: ClassVar[float] = 0.98
    DEFAULT_REBALANCE_DAYS: ClassVar[int] = 15

    _SEED: ClassVar[tuple[str, ...]] = (
        "ADANIPOWER", "SHRIRAMFIN", "HINDALCO", "ADANIGREEN", "EICHERMOT",
        "ADANIENSOL", "IDEA", "BHEL", "CUMMINSIND", "POWERINDIA",
        "POLYCAB", "MUTHOOTFIN", "PAYTM", "INDIANB", "LAURUSLABS",
        "VEDL", "BHARATFORG", "NYKAA", "ASHOKLEY", "MCX",
        "FEDERALBNK", "AUBANK", "LTF", "SAIL", "GLENMARK",
        "FORTIS", "NATIONALUM", "BSE", "ABCAPITAL", "DIXON",
    )

    # ------------------------------------------------------------------ #
    # Seed injection – guarantees CI never fails on resolve_universe
    # ------------------------------------------------------------------ #
    @classmethod
    def _ensure_registered(cls) -> None:
        if cls.UNIVERSE_KEY not in UNIVERSES:
            UNIVERSES[cls.UNIVERSE_KEY] = cls._SEED

    @classmethod
    def _resolve(cls, venue: str = "NSE") -> Set[InstrumentId]:
        cls._ensure_registered()
        return set(resolve_universe(cls.UNIVERSE_KEY, venue=venue))

    # ------------------------------------------------------------------ #
    # Construction – reads the generic config keys that every α‑30 strategy
    # needs (capital, allocation, rebalance cadence, venue).
    # ------------------------------------------------------------------ #
    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.capital: float = float(p.get("capital", self.DEFAULT_CAPITAL))
        self.allocation: float = float(
            p.get("allocation", self.DEFAULT_ALLOCATION)
        )
        self.rebalance_days: int = int(
            p.get("rebalance_days", self.DEFAULT_REBALANCE_DAYS)
        )
        self.venue: str = config.venue or "NSE"

        # State managed by the generic logic
        self._universe: Set[InstrumentId] = self._resolve(self.venue)
        self._last_prices: dict[InstrumentId, float] = {}
        self._last_day: date | None = None
        self._days_since: int = 0
        self._initial_done: bool = False

    @property
    def universe(self) -> Set[InstrumentId]:
        return self._universe

    @universe.setter
    def universe(self, val: Any) -> None:
        self._universe = set(val) if not isinstance(val, set) else val

    # ------------------------------------------------------------------ #
    # Lifecycle hooks (shared across all alphas)
    # ------------------------------------------------------------------ #
    def on_start(self) -> None:
        if not self._universe:
            self._universe = self._resolve(self.venue)

    def on_bar(self, bar: Bar) -> None:
        self._last_prices[bar.instrument_id] = float(bar.close)

        day = self._bar_day(bar, self.ctx.now())
        day_changed = False
        if self._last_day is None:
            self._last_day = day
        elif day > self._last_day:
            self._days_since += 1
            self._last_day = day
            day_changed = True

        if not self._initial_done:
            if len(self._last_prices) >= len(self._universe) or day_changed:
                self._rebalance()
                self._initial_done = True
                self._days_since = 0
            return

        if self._days_since >= self.rebalance_days:
            self._rebalance()
            self._days_since = 0

    # ------------------------------------------------------------------ #
    # Helper: portfolio valuation (used by many alphas)
    # ------------------------------------------------------------------ #
    def _portfolio_value(self) -> float:
        """Cash + mark‑to‑market of every open position."""
        value = float(self.ctx.cash()) if self.ctx else 0.0
        for iid, qty in self.ctx.positions().items():
            if qty == 0:
                continue
            price = self._last_prices.get(iid)
            if price is not None and price > 0:
                value += qty * price
        if value <= 0:
            value = self.capital
        return value

    # ------------------------------------------------------------------ #
    # Helper: convert a Bar into a date (UTC) – identical to the original.
    # ------------------------------------------------------------------ #
    @staticmethod
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

    # ------------------------------------------------------------------ #
    # Abstract rebalance – concrete subclasses implement their own logic.
    # ------------------------------------------------------------------ #
    def _rebalance(self) -> None:
        raise NotImplementedError(
            "Sub‑class must implement its own rebalance routine"
        )
