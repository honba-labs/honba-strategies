"""Bollinger breakout: long-only band breakout above the Ichimoku cloud.

Buy a close above the upper Bollinger band (computed on the bar's (high+low)/2)
while above both cloud spans; exit fully on a close below the middle band.
The cloud is the standard displaced Ichimoku (spans computed ``displacement``
bars ago). Costs are applied by the Honba backtest engine, not here.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Bollinger, Ichimoku
from honba.strategies.sizing import whole_shares


class BollingerBreakout(Strategy):
    name = "bollinger_breakout"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.period, self.mult = int(p["period"]), float(p["mult"])
        self.tenkan, self.kijun = int(p["tenkan"]), int(p["kijun"])
        self.senkou_b, self.displacement = int(p["senkou_b"]), int(p["displacement"])
        if self.period < 2:
            raise ValueError("period must be >= 2")
        if not self.mult > 0:
            raise ValueError("mult must be positive")
        if min(self.tenkan, self.kijun, self.senkou_b, self.displacement) < 1:
            raise ValueError("ichimoku periods and displacement must be positive")
        self._bb = Bollinger(self.period, self.mult)
        self._cloud = Ichimoku(self.tenkan, self.kijun, self.senkou_b, self.displacement)

    def on_bar(self, bar: Bar) -> None:
        bb = self._bb.update((bar.high + bar.low) / 2)
        cloud = self._cloud.update(bar.high, bar.low)
        if bb is None or cloud is None:
            return
        held = self.position(self.instrument_id)
        if held == 0 and bar.close > max(cloud) and bar.close > bb.upper:
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self.buy(self.instrument_id, qty)
        elif held > 0 and bar.close < bb.middle:
            self.sell(self.instrument_id, held)
