"""Strategy: alpha30_factor

An equal-weighted portfolio strategy configuring 30 equities from the
NSE NIFTY 200 ALPHA 30 index. Rebalances every 15th open trading day, allocating
equal capital weight to each constituent.
"""
from __future__ import annotations

import math
from typing import ClassVar

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.markets.india.universes import resolve_universe
from honba.strategies.base import Strategy
from honba.strategies.config import StrategyConfig


class Alpha30Factor(Strategy):
    name: ClassVar[str] = "alpha30_factor"

    def __init__(self, config: StrategyConfig) -> None:
        p = config.params
        self.capital = float(p.get("capital", 1_000_000.0))
        self.rebalance_days = int(p.get("rebalance_days", 15))
        self.universe_name = str(p.get("universe_name", "nifty200_alpha_30"))
        self.max_equities = int(p.get("max_equities", 30))

        try:
            self.universe = resolve_universe(self.universe_name, venue=config.venue)[: self.max_equities]
        except Exception:
            self.universe = [InstrumentId(config.symbol, config.venue)]

        self._target_set = {inst.symbol: inst for inst in self.universe}
        self._latest_prices: dict[InstrumentId, float] = {}
        self._current_session_ts: int | None = None
        self._open_day_count: int = 0
        self._bars_this_day: dict[InstrumentId, Bar] = {}

    def on_bar(self, bar: Bar) -> None:
        inst = bar.instrument_id
        self._latest_prices[inst] = bar.close

        # Group bars into calendar trading sessions (by day timestamp / IST day)
        bar_day = bar.ts // 86_400_000_000_000
        if self._current_session_ts is None:
            self._current_session_ts = bar_day
            self._open_day_count = 1
            self._bars_this_day = {inst: bar}
        elif bar_day != self._current_session_ts:
            self._current_session_ts = bar_day
            self._open_day_count += 1
            self._bars_this_day = {inst: bar}
        else:
            self._bars_this_day[inst] = bar

        # Check if rebalance is due today (e.g. day 1, day 16, day 31, etc.)
        if (self._open_day_count - 1) % self.rebalance_days == 0:
            # Execute once all available universe bars for today have arrived or last constituent
            if len(self._bars_this_day) >= len(self.universe) or inst == self.universe[-1]:
                self._execute_rebalance()



    def _execute_rebalance(self) -> None:
        """Rebalance portfolio to equal weights across all constituents."""
        active_universe = [i for i in self.universe if i in self._latest_prices and self._latest_prices[i] > 0]
        if not active_universe:
            return

        weight_per_asset = 1.0 / len(active_universe)
        target_capital_per_asset = self.capital * weight_per_asset

        # 1. Rebalance existing positions / sell if excess or not in universe
        for inst, held in list(self.ctx.positions().items()):
            if held <= 0:
                continue
            if inst not in active_universe:
                if not self.busy(inst):
                    self.sell(inst, held)
            else:
                price = self._latest_prices[inst]
                target_qty = math.floor(target_capital_per_asset / price)
                diff = target_qty - held
                if diff < 0 and not self.busy(inst):
                    self.sell(inst, abs(diff))

        # 2. Buy up to target quantity for each asset
        for inst in active_universe:
            if self.busy(inst):
                continue
            price = self._latest_prices[inst]
            held = self.position(inst)
            target_qty = math.floor(target_capital_per_asset / price)
            diff = target_qty - held
            if diff > 0:
                self.buy(inst, diff)
