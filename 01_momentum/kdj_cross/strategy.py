"""KDJ cross: long-only stochastic (KDJ) momentum entry.

Buy when J is above both K and D. Exit fully when in profit and J turns down,
or when J drops below K or D, or when the bar low touches a protective stop of
``atr_mult`` x ATR below the entry. Costs are applied by the Honba engine.
"""
from honba.entities.bar import Bar
from honba.entities.order import OrderSide
from honba.entities.trade import Trade
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Atr, Kdj
from honba.strategies.sizing import whole_shares


class KdjCross(Strategy):
    name = "kdj_cross"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.fastk, self.slowk, self.slowd = int(p["fastk"]), int(p["slowk"]), int(p["slowd"])
        self.atr_period, self.atr_mult = int(p["atr_period"]), float(p["atr_mult"])
        if min(self.fastk, self.slowk, self.slowd, self.atr_period) < 1:
            raise ValueError("fastk, slowk, slowd and atr_period must be positive")
        if not self.atr_mult > 0:
            raise ValueError("atr_mult must be positive")
        self._kdj = Kdj(self.fastk, self.slowk, self.slowd)
        self._atr = Atr(self.atr_period)
        self._prev_j: float | None = None
        self._entry = self._stop = None

    def on_bar(self, bar: Bar) -> None:
        kdj, atr = self._kdj.update(bar.high, bar.low, bar.close), self._atr.update(bar.high, bar.low, bar.close)
        if kdj is None:
            return
        k, d, j = kdj
        prev_j, self._prev_j = self._prev_j, j
        held = self.position(self.instrument_id)
        if self.busy(self.instrument_id):
            return  # an order is still unfilled
        if held == 0:
            if j > k and j > d and atr is not None:
                qty = whole_shares(self.capital, self.allocation, bar.close)
                if qty > 0:
                    self.buy(self.instrument_id, qty)
        else:
            in_profit = self._entry is not None and bar.close > self._entry
            stopped = self._stop is not None and bar.low <= self._stop
            turned_down = in_profit and prev_j is not None and prev_j > j
            if stopped or turned_down or j < k or j < d:
                self.sell(self.instrument_id, held)

    def on_fill(self, fill: Trade) -> None:
        if fill.side is OrderSide.BUY:
            atr = self._atr.value
            self._entry = fill.price
            self._stop = fill.price - self.atr_mult * atr if atr is not None else None
        else:
            self._entry = self._stop = None
