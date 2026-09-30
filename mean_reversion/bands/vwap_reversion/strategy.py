"""VWAP reversion: intraday long-only mean reversion to the session VWAP (NSE, IST).

Buy when the close is below the lower VWAP band (before ``entry_cutoff``); exit when the
close returns to VWAP, or at ``squareoff`` (intraday product: no carrying overnight). If a
position is still open when a new IST session starts (missing bars), it is closed on the
first bar of that session. VWAP resets each IST session day; the indicator and its
parameters come from ``[indicators.vwap]``. Costs are applied by the Honba backtest engine.
"""
from honba.entities.bar import Bar
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import IndicatorBank
from honba.strategies.indicators._india import hhmm_to_minutes, ist_minute_of_day, ist_session_day
from honba.strategies.sizing import whole_shares


class VwapReversion(Strategy):
    name = "vwap_reversion"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.instrument_id = config.instrument_id
        self.capital, self.allocation = float(p["capital"]), float(p["allocation"])
        if not self.capital > 0:
            raise ValueError("capital must be positive")
        if not 0 < self.allocation <= 1:
            raise ValueError("allocation must be in (0, 1]")
        self.entry_cutoff = hhmm_to_minutes(str(p["entry_cutoff"]))
        self.squareoff = hhmm_to_minutes(str(p["squareoff"]))
        if not self.entry_cutoff < self.squareoff:
            raise ValueError("entry_cutoff must be before squareoff")
        self.ind = IndicatorBank(config.indicators)
        if "vwap" not in self.ind.names:
            raise ValueError("config needs an [indicators.vwap] vwap")
        self._day: int | None = None

    def on_bar(self, bar: Bar) -> None:
        day, minute = ist_session_day(bar.ts), ist_minute_of_day(bar.ts)
        v = self.ind.update(bar)["vwap"]
        new_session = self._day is not None and day != self._day
        self._day = day
        if self.busy(self.instrument_id):
            return
        held = self.position(self.instrument_id)
        if held > 0:
            if new_session or minute >= self.squareoff or bar.close >= v.vwap:
                self.sell(self.instrument_id, held)
        elif minute < self.entry_cutoff and bar.close < v.lower:
            qty = whole_shares(self.capital, self.allocation, bar.close)
            if qty > 0:
                self.buy(self.instrument_id, qty)
