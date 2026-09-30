"""MACD trend: long-only MACD/EMA trend follower for NSE cash equities.

Buy when MACD is above its signal line and the close is above the trend EMA;
exit fully when MACD is below signal AND the close is below the EMA.
Costs are applied by the Honba backtest engine, not here.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Ema, Macd
from honba.strategies.sizing import whole_shares


class MacdTrend(Strategy):
    name = "macd_trend"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.ema_period, self.fast, self.slow = int(p["ema"]), int(p["fastperiod"]), int(p["slowperiod"])
        self.signal = int(p["signal"])
        if self.ema_period < 1 or self.signal < 1:
            raise ValueError("ema and signal must be positive")
        if not 0 < self.fast < self.slow:
            raise ValueError("fastperiod must be positive and less than slowperiod")
        seed = str(p.get("seed", "sma"))  # "first" reproduces Jesse's EMA seeding
        self._ema = Ema(self.ema_period, seed)
        self._macd = Macd(self.fast, self.slow, self.signal, seed)

    def on_bar(self, bar: Bar) -> None:
        ema, m = self._ema.update(bar.close), self._macd.update(bar.close)
        if ema is None or m is None:
            return
        held = self.position(self.instrument_id)
        if self.busy(self.instrument_id):
            return  # an order is still unfilled
        if held == 0 and bar.close > ema and m.macd > m.signal:
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self.buy(self.instrument_id, qty)
        elif held > 0 and m.macd < m.signal and bar.close < ema:
            self.sell(self.instrument_id, held)
