"""KDJ cross: long-only stochastic (KDJ) momentum entry.

Buy when J is above both K and D. Exit fully when in profit and J turns down,
or when J drops below K or D, or when the bar low touches a protective stop of
``atr_mult`` x ATR below the entry. Costs are applied by the Honba engine.
"""
from collections import deque

from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
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


class Kdj:
    """Stochastic KDJ: RSV over ``fastk`` bars, K = SMA(RSV), D = SMA(K), J = 3K - 2D.
    RSV is 0 on a flat window. ``update`` returns ``(k, d, j)`` or None until warm."""

    def __init__(self, fastk: int = 9, slowk: int = 3, slowd: int = 3) -> None:
        self._h: deque[float] = deque(maxlen=fastk)
        self._l: deque[float] = deque(maxlen=fastk)
        self._rsv: deque[float] = deque(maxlen=slowk)
        self._k: deque[float] = deque(maxlen=slowd)

    def update(self, high: float, low: float, close: float):
        self._h.append(high)
        self._l.append(low)
        if len(self._h) < self._h.maxlen:
            return None
        hh, ll = max(self._h), min(self._l)
        self._rsv.append((close - ll) / (hh - ll) * 100 if hh != ll else 0.0)
        if len(self._rsv) < self._rsv.maxlen:
            return None
        self._k.append(sum(self._rsv) / len(self._rsv))
        if len(self._k) < self._k.maxlen:
            return None
        k, d = self._k[-1], sum(self._k) / len(self._k)
        return k, d, 3 * k - 2 * d


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
        self._atr = _Atr(self.atr_period)
        self._prev_j: float | None = None
        self._entry = self._stop = None

    def on_bar(self, bar: Bar) -> None:
        kdj, atr = self._kdj.update(bar.high, bar.low, bar.close), self._atr.update(bar)
        if kdj is None:
            return
        k, d, j = kdj
        prev_j, self._prev_j = self._prev_j, j
        held = self.position(self.instrument_id)
        if held == 0:
            if j > k and j > d and atr is not None:
                qty = whole_shares(self.capital, self.allocation, bar.close)
                if qty > 0:
                    self._entry, self._stop = bar.close, bar.close - self.atr_mult * atr
                    self.buy(self.instrument_id, qty)
        else:
            in_profit = self._entry is not None and bar.close > self._entry
            stopped = self._stop is not None and bar.low <= self._stop
            turned_down = in_profit and prev_j is not None and prev_j > j
            if stopped or turned_down or j < k or j < d:
                self._entry = self._stop = None
                self.sell(self.instrument_id, held)
