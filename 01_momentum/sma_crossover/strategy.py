"""SMA crossover: long-only trend follower for NSE cash equities.

Buy when the fast SMA is above the slow SMA while flat; exit fully when it
falls below. NSE equity is spot, so there is no short leg. Costs (STT, GST,
stamp duty) and slippage are applied by the Honba backtest engine, not here.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import Sma
from honba.strategies.sizing import whole_shares


class SmaCrossover(Strategy):
    name = "sma_crossover"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.fast_period, self.slow_period = int(p["fast"]), int(p["slow"])
        if not 0 < self.fast_period < self.slow_period:
            raise ValueError("fast must be positive and less than slow")
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        self._fast, self._slow = Sma(self.fast_period), Sma(self.slow_period)

    def on_bar(self, bar: Bar) -> None:
        fast, slow = self._fast.update(bar.close), self._slow.update(bar.close)
        if fast is None or slow is None:
            return
        held = self.position(self.instrument_id)
        if held == 0 and fast > slow:
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self.buy(self.instrument_id, qty)
        elif held > 0 and fast < slow:
            self.sell(self.instrument_id, held)
