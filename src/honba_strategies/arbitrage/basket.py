"""Basket Arbitrage Strategy (Index/ETF vs Synthetic Basket).

Monitors price discrepancy between index ETF (e.g. NIFTYBEES) and synthetic basket
of underlying constituents. Executes synchronized basket creation/redemption arbitrage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import ArbitrageStrategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class BasketConfig(BaseStrategyConfig):
    """Configuration for Basket Arbitrage Strategy."""

    # ETF leg
    etf_symbol: str = ""
    etf_exchange: str = ""

    # Constituent symbols (NIFTY 50) - empty by default, must be provided by caller
    constituents: list[str] = field(default_factory=list)

    # Arbitrage parameters
    min_basis_bps: Decimal = Decimal("10")  # 10 bps minimum
    max_basis_bps: Decimal = Decimal("100")  # Max expected basis
    rebalance_threshold_bps: Decimal = Decimal("5")  # Rebalance drift threshold

    # Execution parameters
    etf_lot_size: int = 1
    max_positions: int = 3

    # Risk parameters
    max_holding_days: int = 30
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "basket",
        "category": "arbitrage",
        "description": "Index ETF vs synthetic basket creation/redemption arbitrage",
        "tags": ["arbitrage", "basket", "etf", "index"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if len(self.constituents) < 10:
            raise ValueError("Need at least 10 constituents for basket arbitrage")


@register_strategy("basket", "arbitrage", tags=["arbitrage", "basket", "etf", "index"])
class BasketArbitrageStrategy(ArbitrageStrategy):
    """Index ETF vs synthetic basket arbitrage."""

    name = "basket"
    Config = BasketConfig

    def __init__(self, config: BasketConfig) -> None:
        super().__init__(
            entry_spread=config.min_basis_bps / Decimal("10000"),
            exit_spread=config.rebalance_threshold_bps / Decimal("10000"),
            hedge_ratio=Decimal("1.0"),
            leg_quantity=Decimal("1"),
        )

        self.config = config

        # Runtime state
        self._etf_price: float | None = None
        self._constituent_prices: dict[str, float] = {}
        self._weights: dict[str, Decimal] = {}
        self._active = False

    def on_start(self) -> None:
        """Initialize instrument IDs and weights."""
        from honba.entities.instrument import InstrumentId

        self.etf_id = InstrumentId(self.config.etf_symbol, self.config.etf_exchange)
        self.constituent_ids = {
            sym: InstrumentId(sym, "NSE") for sym in self.config.constituents
        }

        # Equal-weight by default (in production, use actual index weights)
        weight = Decimal("1") / Decimal(str(len(self.config.constituents)))
        self._weights = {sym: weight for sym in self.config.constituents}

    def on_bar(self, bar) -> None:
        """Process bars for ETF and constituents."""
        if bar.instrument_id == self.etf_id:
            self._etf_price = float(bar.close)
        elif bar.instrument_id in self.constituent_ids.values():
            # Find symbol for this instrument
            for sym, iid in self.constituent_ids.items():
                if iid == bar.instrument_id:
                    self._constituent_prices[sym] = float(bar.close)
                    break

        # Evaluate when we have ETF price and most constituent prices
        if self._etf_price is not None and len(self._constituent_prices) >= len(self.config.constituents) * 0.8:
            self._evaluate_basket()

    def _calculate_synthetic_basket_price(self) -> float:
        """Calculate synthetic basket price from constituents."""
        total = 0.0
        for sym, weight in self._weights.items():
            price = self._constituent_prices.get(sym)
            if price is not None:
                total += float(weight) * price
        return total

    def _evaluate_basket(self) -> None:
        """Evaluate ETF vs synthetic basket discrepancy."""
        if self._etf_price is None:
            return

        synthetic = self._calculate_synthetic_basket_price()
        if synthetic <= 0:
            return

        basis_bps = (self._etf_price - synthetic) / synthetic * 10000
        threshold_bps = float(self.config.min_basis_bps)

        if abs(basis_bps) < threshold_bps:
            return

        if basis_bps > threshold_bps and not self._active:
            # ETF expensive relative to basket - sell ETF, buy basket
            self._execute_arbitrage("ETF_EXPENSIVE", basis_bps)
        elif basis_bps < -threshold_bps and not self._active:
            # ETF cheap relative to basket - buy ETF, sell basket
            self._execute_arbitrage("ETF_CHEAP", basis_bps)
        elif self._active:
            # Check exit condition
            if abs(basis_bps) < float(self.config.rebalance_threshold_bps):
                self._unwind_arbitrage()

    def _execute_arbitrage(self, direction: str, basis_bps: float) -> None:
        """Execute creation/redemption arbitrage."""
        self._active = True
        self.log_event("BASKET_ARBITRAGE_ENTRY", direction=direction, basis_bps=basis_bps)

        # In production, this would execute synchronized orders:
        # - ETF creation/redemption with AMC
        # - Synchronized constituent trades
        # For now, log the intent
        qty = self.config.etf_lot_size

        if direction == "ETF_EXPENSIVE":
            # Sell ETF, buy constituents
            self.sell(self.etf_id, qty)
            for sym, iid in self.constituent_ids.items():
                weight = self._weights[sym]
                const_qty = int(qty * float(weight) * self._etf_price / self._constituent_prices.get(sym, 1))
                if const_qty > 0:
                    self.buy(iid, const_qty)
        elif direction == "ETF_CHEAP":
            # Buy ETF, sell constituents
            self.buy(self.etf_id, qty)
            for sym, iid in self.constituent_ids.items():
                weight = self._weights[sym]
                const_qty = int(qty * float(weight) * self._etf_price / self._constituent_prices.get(sym, 1))
                if const_qty > 0:
                    self.sell(iid, const_qty)

    def _unwind_arbitrage(self) -> None:
        """Unwind arbitrage position."""
        # In production, execute opposite trades
        self._active = False
        self.log_event("BASKET_ARBITRAGE_EXIT", reason="BASIS_CONVERGED")