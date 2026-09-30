"""Supertrend follow: long-only trend following on the Supertrend indicator.

Buy while Supertrend is in an uptrend and the strategy is flat; exit fully when it
flips to a downtrend. NSE cash equity has no short leg. The indicator and its parameters
come from ``[indicators.trend]`` in ``config.toml``. Costs (STT, GST, stamp duty) and
slippage are applied by the Honba backtest engine, not here.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import IndicatorBank
from honba.strategies.sizing import whole_shares


class SupertrendFollow(Strategy):
    name = "supertrend_follow"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.ind = IndicatorBank(config.indicators)
        if "trend" not in self.ind.names:
            raise ValueError("config needs an [indicators.trend] supertrend")

    def on_bar(self, bar: Bar) -> None:
        trend = self.ind.update(bar)["trend"]
        if trend is None or self.busy(self.instrument_id):
            return  # warming up, or an order is still unfilled
        held = self.position(self.instrument_id)
        if held == 0 and trend.direction > 0:
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self.buy(self.instrument_id, qty)
        elif held > 0 and trend.direction < 0:
            self.sell(self.instrument_id, held)
