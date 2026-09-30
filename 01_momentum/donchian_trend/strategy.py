"""Donchian trend: long-only channel breakout with an SMA trend filter.

Buy a close above the previous N-bar high while above the trend SMA; exit
fully on a close below the previous N-bar low. Costs are applied by the Honba
backtest engine, not here.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Donchian, Sma
from honba.strategies.sizing import whole_shares


class DonchianTrend(Strategy):
    name = "donchian_trend"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.period, self.trend_sma = int(p["period"]), int(p["trend_sma"])
        if self.period < 1 or self.trend_sma < 1:
            raise ValueError("period and trend_sma must be positive")
        self._chan, self._sma = Donchian(self.period), Sma(self.trend_sma)
        self._prev = None  # channel of the bars before the current one

    def on_bar(self, bar: Bar) -> None:
        prev, self._prev = self._prev, self._chan.update(bar.high, bar.low)
        sma = self._sma.update(bar.close)
        if prev is None or sma is None:
            return
        held = self.position(self.instrument_id)
        if held == 0 and bar.close > sma and bar.close > prev.upper:
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self.buy(self.instrument_id, qty)
        elif held > 0 and bar.close < prev.lower:
            self.sell(self.instrument_id, held)
