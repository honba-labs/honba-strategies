"""RSI(2) mean reversion, long leg only.

Buy when RSI(2) <= ``oversold`` while the close is above the trend SMA; exit
fully once the close is above the short exit SMA. Costs are applied by the
Honba backtest engine, not here.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Rsi, Sma
from honba.strategies.sizing import whole_shares


class Rsi2Connors(Strategy):
    name = "rsi2_connors"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.oversold = float(p["oversold"])
        self.trend_sma, self.exit_sma = int(p["trend_sma"]), int(p["exit_sma"])
        if not 0 < self.oversold < 100:
            raise ValueError("oversold must be in (0, 100)")
        if self.trend_sma < 1 or self.exit_sma < 1:
            raise ValueError("trend_sma and exit_sma must be positive")
        self._rsi, self._trend, self._exit = Rsi(2), Sma(self.trend_sma), Sma(self.exit_sma)

    def on_bar(self, bar: Bar) -> None:
        rsi, trend, exit_ma = self._rsi.update(bar.close), self._trend.update(bar.close), self._exit.update(bar.close)
        held = self.position(self.instrument_id)
        if held == 0:
            if rsi is not None and trend is not None and bar.close > trend and rsi <= self.oversold:
                qty = whole_shares(self.capital, self.allocation, bar.close)
                if qty > 0:
                    self.buy(self.instrument_id, qty)
        elif exit_ma is not None and bar.close > exit_ma:
            self.sell(self.instrument_id, held)
