"""Turtle System 1 (simplified): long-only, no pyramiding.

Buy a break of the previous ``entry``-bar high; exit on a close below the
previous ``exit``-bar low, or when the bar low touches a protective stop of
``atr_mult`` x ATR below the entry. Costs are applied by the Honba engine.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Donchian
from honba.strategies.sizing import whole_shares


class _Atr:
    """Wilder ATR over high/low/close; first value after ``period`` true ranges."""

    def __init__(self, period: int) -> None:
        self.period = period
        self._prev_close: float | None = None
        self._trs: list[float] = []
        self.value: float | None = None

    def update(self, bar: Bar) -> float | None:
        if self._prev_close is None:
            tr = None
        else:
            pc = self._prev_close
            tr = max(bar.high - bar.low, abs(bar.high - pc), abs(bar.low - pc))
        self._prev_close = bar.close
        if tr is None:
            return None
        if self.value is not None:
            self.value = (self.value * (self.period - 1) + tr) / self.period
        else:
            self._trs.append(tr)
            if len(self._trs) == self.period:
                self.value = sum(self._trs) / self.period
        return self.value


class Turtle20(Strategy):
    name = "turtle_20"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.entry, self.exit = int(p["entry"]), int(p["exit"])
        self.atr_period, self.atr_mult = int(p["atr_period"]), float(p["atr_mult"])
        if min(self.entry, self.exit, self.atr_period) < 1:
            raise ValueError("entry, exit and atr_period must be positive")
        if not self.atr_mult > 0:
            raise ValueError("atr_mult must be positive")
        self._entry_ch, self._exit_ch = Donchian(self.entry), Donchian(self.exit)
        self._atr = _Atr(self.atr_period)
        self._prev_entry = self._prev_exit = None
        self._stop: float | None = None

    def on_bar(self, bar: Bar) -> None:
        pe, self._prev_entry = self._prev_entry, self._entry_ch.update(bar.high, bar.low)
        px, self._prev_exit = self._prev_exit, self._exit_ch.update(bar.high, bar.low)
        atr = self._atr.update(bar)
        held = self.position(self.instrument_id)
        if held > 0:
            if (self._stop is not None and bar.low <= self._stop) or (px is not None and bar.close < px.lower):
                self._stop = None
                self.sell(self.instrument_id, held)
        elif pe is not None and atr is not None and bar.close > pe.upper:
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self._stop = bar.close - self.atr_mult * atr
                self.buy(self.instrument_id, qty)
