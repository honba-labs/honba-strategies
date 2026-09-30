"""IFR2: RSI(2) dip buying above the Ichimoku cloud, long only.

Buy when RSI(2) < ``oversold`` while the close is above both cloud spans; exit
fully when the close is above the highs of the two previous bars. The cloud is
the standard displaced Ichimoku (spans computed ``displacement`` bars ago).
Costs are applied by the Honba backtest engine, not here.
"""
from collections import deque

from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Ichimoku, Rsi
from honba.strategies.sizing import whole_shares


class Ifr2(Strategy):
    name = "ifr2"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.oversold = float(p["oversold"])
        self.tenkan, self.kijun = int(p["tenkan"]), int(p["kijun"])
        self.senkou_b, self.displacement = int(p["senkou_b"]), int(p["displacement"])
        if not 0 < self.oversold < 100:
            raise ValueError("oversold must be in (0, 100)")
        if min(self.tenkan, self.kijun, self.senkou_b, self.displacement) < 1:
            raise ValueError("ichimoku periods and displacement must be positive")
        self._rsi = Rsi(2)
        self._cloud = Ichimoku(self.tenkan, self.kijun, self.senkou_b, self.displacement)
        self._highs: deque[float] = deque(maxlen=2)  # highs of the two previous bars

    def on_bar(self, bar: Bar) -> None:
        rsi = self._rsi.update(bar.close)
        cloud = self._cloud.update(bar.high, bar.low)
        prior_highs = list(self._highs)
        self._highs.append(bar.high)
        held = self.position(self.instrument_id)
        if held == 0:
            if rsi is not None and cloud is not None and bar.close > max(cloud) and rsi < self.oversold:
                qty = whole_shares(self.capital, self.allocation, bar.close)
                if qty > 0:
                    self.buy(self.instrument_id, qty)
        elif len(prior_highs) == 2 and bar.close > max(prior_highs):
            self.sell(self.instrument_id, held)
