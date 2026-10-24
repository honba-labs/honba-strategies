"""Cash-and-Carry Basis Arbitrage Strategy.

Ingests spot equity (NSE) and near-month equity futures (NFO).
Detects mispriced basis exceeding financing cost + statutory taxes (STT, GST, Stamp Duty).
Long delivery equity (CNC), short near-month future; hold until expiry settlement at parity.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from honba.strategies.base import ArbitrageStrategy
from honba_strategies.core.config import BaseStrategyConfig
from honba_strategies.core.registry import register_strategy


@dataclass
class CashAndCarryConfig(BaseStrategyConfig):
    """Configuration for Cash-and-Carry Basis Arbitrage."""

    # Spot leg (equity)
    spot_symbol: str = ""
    spot_exchange: str = ""

    # Futures leg (near-month)
    futures_symbol: str = ""
    futures_exchange: str = ""
    futures_expiry: str = ""  # Format: YYYY-MM-DD

    # Cost parameters (annualized)
    risk_free_rate: Decimal = Decimal("0.065")  # 6.5% annual
    stt_rate: Decimal = Decimal("0.001")  # 0.1% STT on delivery
    gst_rate: Decimal = Decimal("0.18")  # 18% GST
    stamp_duty_rate: Decimal = Decimal("0.00015")  # 0.015% stamp duty

    # Basis threshold (minimum basis to enter trade)
    min_basis_bps: Decimal = Decimal("50")  # 50 bps minimum

    # Position sizing
    lot_size: int = 250  # Futures lot size
    max_positions: int = 5

    # Risk parameters
    max_holding_days: int = 90
    freeze_limit: int = 1800

    _registry_meta: ClassVar[dict] = {
        "name": "cash_and_carry",
        "category": "arbitrage",
        "description": "Cash-and-carry basis arbitrage: long spot equity, short near-month futures",
        "tags": ["arbitrage", "cash_and_carry", "basis", "futures"],
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.futures_expiry:
            raise ValueError("futures_expiry must be specified (YYYY-MM-DD)")
        if not self.spot_symbol or not self.futures_symbol:
            raise ValueError("Both spot_symbol and futures_symbol must be specified")


@register_strategy("cash_and_carry", "arbitrage", tags=["arbitrage", "cash_and_carry", "basis", "futures"])
class CashAndCarryStrategy(ArbitrageStrategy):
    """Cash-and-carry basis arbitrage: long spot, short futures."""

    name = "cash_and_carry"
    Config = CashAndCarryConfig

    def __init__(self, config: CashAndCarryConfig) -> None:
        # Initialize base with spread parameters (basis in price terms)
        super().__init__(
            entry_spread=config.min_basis_bps / Decimal("10000"),  # Convert bps to price
            exit_spread=Decimal("0.0001"),  # Exit near parity
            hedge_ratio=Decimal("1.0"),
            leg_quantity=Decimal(str(config.lot_size)),
        )

        self.config = config

        # Runtime state
        self._active_positions: dict[str, dict] = {}
        self._days_in_positions: dict[str, int] = {}

    def on_start(self) -> None:
        """Initialize instrument IDs."""
        from honba.entities.instrument import InstrumentId

        self.spot_id = InstrumentId(self.config.spot_symbol, self.config.spot_exchange)
        self.futures_id = InstrumentId(self.config.futures_symbol, self.config.futures_exchange)

    def on_bar(self, bar) -> None:
        """Process bars for spot and futures."""
        if bar.instrument_id not in (self.spot_id, self.futures_id):
            return

        # Only evaluate when we have both prices
        if hasattr(self, '_last_spot_price') and hasattr(self, '_last_futures_price'):
            self._evaluate_basis()

        if bar.instrument_id == self.spot_id:
            self._last_spot_price = float(bar.close)
        elif bar.instrument_id == self.futures_id:
            self._last_futures_price = float(bar.close)

    def _calculate_fair_basis(self, spot_price: float, days_to_expiry: int) -> Decimal:
        """Calculate theoretical fair basis including all costs."""
        if days_to_expiry <= 0:
            return Decimal("0")

        r = float(self.config.risk_free_rate)
        t = days_to_expiry / 365.0

        # Theoretical futures price: S * e^(r*t)
        fair_futures = spot_price * (1 + r * t)  # Simple approximation

        # Add transaction costs
        stt_cost = spot_price * float(self.config.stt_rate)
        gst_cost = spot_price * float(self.config.gst_rate) * 0.001  # On brokerage
        stamp_cost = spot_price * float(self.config.stamp_duty_rate)

        total_cost = stt_cost + gst_cost + stamp_cost
        fair_futures += total_cost

        basis = fair_futures - spot_price
        return Decimal(str(basis))

    def _get_days_to_expiry(self) -> int:
        """Calculate days to futures expiry."""
        from datetime import datetime, date
        expiry = datetime.strptime(self.config.futures_expiry, "%Y-%m-%d").date()
        days = (expiry - date.today()).days
        return max(0, days)

    def _evaluate_basis(self) -> None:
        """Evaluate basis and execute if mispriced."""
        if not hasattr(self, '_last_spot_price') or not hasattr(self, '_last_futures_price'):
            return

        spot = self._last_spot_price
        futures = self._last_futures_price
        days = self._get_days_to_expiry()

        if days <= 0:
            # Expiry approaching - close positions
            self._close_all_positions()
            return

        fair_basis = self._calculate_fair_basis(spot, days)
        actual_basis = Decimal(str(futures - spot))

        # Check if basis is wide enough
        threshold = self.config.min_basis_bps / Decimal("10000") * Decimal(str(spot))

        key = f"{self.config.spot_symbol}_{self.config.futures_expiry}"

        if actual_basis > fair_basis + threshold and key not in self._active_positions:
            # Basis too wide - sell futures, buy spot
            self._enter_position(key, spot, futures)
        elif actual_basis < fair_basis - threshold and key not in self._active_positions:
            # Basis negative/very tight - could reverse (not typical for cash-carry)
            pass
        elif key in self._active_positions:
            # Check exit condition: basis converged to fair value
            if abs(actual_basis - fair_basis) < threshold / Decimal("2"):
                self._exit_position(key)
            elif self._days_in_positions.get(key, 0) >= self.config.max_holding_days:
                self._exit_position(key)

    def _enter_position(self, key: str, spot: float, futures: float) -> None:
        """Enter cash-and-carry: long spot, short futures."""
        qty = self.config.lot_size

        # Long spot (CNC - delivery)
        self.buy(self.spot_id, qty)

        # Short futures (MIS/NRML)
        self.sell(self.futures_id, qty)

        self._active_positions[key] = {
            "entry_spot": spot,
            "entry_futures": futures,
            "entry_basis": futures - spot,
        }
        self._days_in_positions[key] = 0
        self.log_event("CASH_CARRY_ENTRY", key=key, basis=futures - spot)

    def _exit_position(self, key: str) -> None:
        """Exit cash-and-carry: sell spot, buy futures."""
        if key not in self._active_positions:
            return

        pos = self._active_positions.pop(key)
        self._days_in_positions.pop(key, None)

        qty = self.config.lot_size

        # Sell spot, buy futures
        self.sell(self.spot_id, qty)
        self.buy(self.futures_id, qty)

        pnl = (pos["entry_futures"] - self._last_futures_price) * qty - \
              (self._last_spot_price - pos["entry_spot"]) * qty

        self.log_event("CASH_CARRY_EXIT", key=key, pnl=pnl)

    def _close_all_positions(self) -> None:
        """Close all open positions near expiry."""
        for key in list(self._active_positions.keys()):
            self._exit_position(key)

    def on_fill(self, fill) -> None:
        """Track fill days for position management."""
        super().on_fill(fill)
        for key in self._days_in_positions:
            self._days_in_positions[key] += 1