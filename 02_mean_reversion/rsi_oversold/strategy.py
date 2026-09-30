"""RSI oversold: long-only dip buying in an uptrend.

Buy when RSI is below ``entry`` while the close is above the trend SMA
(``trend_sma = 0`` disables the filter). Exit fully once RSI is above ``exit``
or after ``max_hold`` bars. Costs are applied by the Honba engine, not here.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Rsi, Sma
from honba.strategies.sizing import whole_shares


class RsiOversold(Strategy):
    name = "rsi_oversold"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.rsi_period, self.entry, self.exit = int(p["rsi_period"]), float(p["entry"]), float(p["exit"])
        self.trend_sma, self.max_hold = int(p["trend_sma"]), int(p["max_hold"])
        if self.rsi_period < 1 or self.max_hold < 1 or self.trend_sma < 0:
            raise ValueError("rsi_period and max_hold must be positive, trend_sma >= 0")
        if not 0 < self.entry < self.exit < 100:
            raise ValueError("need 0 < entry < exit < 100")
        self._rsi = Rsi(self.rsi_period)
        self._sma = Sma(self.trend_sma) if self.trend_sma else None
        self._bars = 0
        self._entry_bar = 0

    def on_bar(self, bar: Bar) -> None:
        self._bars += 1
        rsi = self._rsi.update(bar.close)
        sma = self._sma.update(bar.close) if self._sma else None
        if rsi is None or (self._sma and sma is None):
            return
        held = self.position(self.instrument_id)
        if held == 0 and rsi < self.entry and (sma is None or bar.close > sma):
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self._entry_bar = self._bars
                self.buy(self.instrument_id, qty)
        elif held > 0 and (rsi > self.exit or self._bars - self._entry_bar >= self.max_hold):
            self.sell(self.instrument_id, held)
