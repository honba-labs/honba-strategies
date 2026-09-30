"""Turtle System 1 (simplified): long-only, no pyramiding.

Buy a break of the previous ``entry``-bar high; exit on a close below the
previous ``exit``-bar low, or when the bar low touches a protective stop of
``atr_mult`` x ATR below the entry. Costs are applied by the Honba engine.
"""
from honba.entities.bar import Bar
from honba.entities.order import OrderSide
from honba.entities.trade import Trade
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Atr, Donchian
from honba.strategies.sizing import whole_shares


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
        self._atr = Atr(self.atr_period)
        self._prev_entry = self._prev_exit = None
        self._stop: float | None = None

    def on_bar(self, bar: Bar) -> None:
        pe, self._prev_entry = self._prev_entry, self._entry_ch.update(bar.high, bar.low)
        px, self._prev_exit = self._prev_exit, self._exit_ch.update(bar.high, bar.low)
        atr = self._atr.update(bar.high, bar.low, bar.close)
        held = self.position(self.instrument_id)
        if self.busy(self.instrument_id):
            return  # an order is still unfilled
        if held > 0:
            if (self._stop is not None and bar.low <= self._stop) or (px is not None and bar.close < px.lower):
                self.sell(self.instrument_id, held)
        elif pe is not None and atr is not None and bar.close > pe.upper:
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self.buy(self.instrument_id, qty)

    def on_fill(self, fill: Trade) -> None:
        if fill.side is OrderSide.BUY:
            atr = self._atr.value
            self._stop = fill.price - self.atr_mult * atr if atr is not None else None
        else:
            self._stop = None
