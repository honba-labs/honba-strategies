"""Indian Regulatory & Microstructure Risk Guards.

Composable risk controls for SEBI compliance, exchange limits, and intraday
microstructure constraints. Can be chained in declarative step.toml pipelines.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from honba.entities.instrument import InstrumentId


@dataclass
class RiskCheckResult:
    """Result of a risk guard check."""

    allowed: bool
    reason: str | None = None
    adjusted_quantity: Decimal | None = None
    adjusted_price: Decimal | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseRiskGuard(ABC):
    """Abstract base class for all risk guards."""

    name: str = "base_guard"

    @abstractmethod
    def check(
        self,
        instrument_id: InstrumentId,
        side: str,  # "BUY" or "SELL"
        quantity: Decimal,
        price: Decimal,
        **kwargs: Any,
    ) -> RiskCheckResult:
        """Check if order passes risk guard.

        Args:
            instrument_id: Instrument being traded
            side: Order side
            quantity: Order quantity
            price: Order price
            **kwargs: Additional context (portfolio, account, etc.)

        Returns:
            RiskCheckResult with allowed flag and optional adjustments
        """
        pass


class SebiAlgoIdGuard(BaseRiskGuard):
    """SEBI Algo ID Enforcement Guard.

    Ensures every order carries a valid SEBI-registered Algo ID.
    Rejects orders without proper algo identification.
    """

    name = "sebi_algo_id"

    def __init__(
        self,
        algo_id: str | None = None,
        require_algo_id: bool = True,
        valid_algo_ids: list[str] | None = None,
    ) -> None:
        """
        Args:
            algo_id: Default algo ID to attach to orders
            require_algo_id: Whether to reject orders without algo ID
            valid_algo_ids: List of valid registered algo IDs
        """
        self.algo_id = algo_id
        self.require_algo_id = require_algo_id
        self.valid_algo_ids = set(valid_algo_ids or [])

    def check(
        self,
        instrument_id: InstrumentId,
        side: str,
        quantity: Decimal,
        price: Decimal,
        algo_id: str | None = None,
        **kwargs: Any,
    ) -> RiskCheckResult:
        effective_algo_id = algo_id or self.algo_id

        if self.require_algo_id and not effective_algo_id:
            return RiskCheckResult(
                allowed=False,
                reason="missing_sebi_algo_id",
                metadata={"required": True},
            )

        if self.valid_algo_ids and effective_algo_id not in self.valid_algo_ids:
            return RiskCheckResult(
                allowed=False,
                reason="invalid_sebi_algo_id",
                metadata={"provided": effective_algo_id, "valid_ids": list(self.valid_algo_ids)},
            )

        return RiskCheckResult(
            allowed=True,
            metadata={"algo_id": effective_algo_id},
        )


class OtrThrottleGuard(BaseRiskGuard):
    """Order-to-Trade Ratio (OTR) Throttling Guard.

    Monitors and enforces exchange OTR limits per algo ID per instrument.
    Tracks order count vs trade count and throttles when ratio approaches limit.
    """

    name = "otr_throttle"

    def __init__(
        self,
        max_otr: int = 100,  # Exchange OTR limit (e.g., 100:1)
        warning_threshold: float = 0.8,  # Warn at 80% of limit
        window_seconds: int = 300,  # Rolling window for OTR calculation
    ) -> None:
        """
        Args:
            max_otr: Maximum allowed order-to-trade ratio
            warning_threshold: Fraction of max_otr at which to warn/throttle
            window_seconds: Rolling window for OTR calculation
        """
        self.max_otr = max_otr
        self.warning_threshold = warning_threshold
        self.window_seconds = window_seconds

        # Per-instrument tracking: {instrument_id: {"orders": int, "trades": int}}
        self._counters: dict[str, dict[str, int]] = {}

    def check(
        self,
        instrument_id: InstrumentId,
        side: str,
        quantity: Decimal,
        price: Decimal,
        algo_id: str | None = None,
        **kwargs: Any,
    ) -> RiskCheckResult:
        key = f"{algo_id or 'default'}:{instrument_id.symbol}"
        counters = self._counters.setdefault(key, {"orders": 0, "trades": 0})

        # Simulate order placement
        projected_orders = counters["orders"] + 1
        projected_trades = max(counters["trades"], 1)  # Avoid div by zero
        projected_otr = projected_orders / projected_trades

        if projected_otr > self.max_otr:
            return RiskCheckResult(
                allowed=False,
                reason="otr_limit_exceeded",
                metadata={
                    "current_otr": counters["orders"] / max(counters["trades"], 1),
                    "max_otr": self.max_otr,
                    "instrument": instrument_id.symbol,
                },
            )

        if projected_otr > self.max_otr * self.warning_threshold:
            return RiskCheckResult(
                allowed=True,
                reason="otr_warning_threshold",
                metadata={
                    "current_otr": counters["orders"] / max(counters["trades"], 1),
                    "projected_otr": projected_otr,
                    "threshold": self.warning_threshold,
                },
            )

        # Increment order counter
        counters["orders"] += 1

        return RiskCheckResult(
            allowed=True,
            metadata={"otr": projected_otr},
        )

    def record_trade(self, instrument_id: InstrumentId, algo_id: str | None = None) -> None:
        """Record a trade execution to update OTR counters."""
        key = f"{algo_id or 'default'}:{instrument_id.symbol}"
        if key in self._counters:
            self._counters[key]["trades"] += 1


class MisSquareOffGuard(BaseRiskGuard):
    """Intraday MIS 15:20 IST Square-Off Guard.

    Enforces mandatory square-off of all MIS (intraday) positions
    by 15:20 IST as per Indian exchange regulations.
    """

    name = "mis_square_off"

    def __init__(
        self,
        square_off_time: str = "15:20",
        warning_minutes: int = 10,
        enforce_on_all_intraday: bool = True,
    ) -> None:
        """
        Args:
            square_off_time: Time in HH:MM format (IST) for mandatory square-off
            warning_minutes: Minutes before square-off to start warning
            enforce_on_all_intraday: Whether to enforce on all intraday positions
        """
        self.square_off_time = square_off_time
        self.warning_minutes = warning_minutes
        self.enforce_on_all_intraday = enforce_on_all_intraday

        # Parse time
        h, m = map(int, square_off_time.split(":"))
        self._square_off_hour = h
        self._square_off_minute = m

    def check(
        self,
        instrument_id: InstrumentId,
        side: str,
        quantity: Decimal,
        price: Decimal,
        current_time: Any = None,  # datetime object
        position_type: str = "MIS",  # "MIS" or "CNC"
        current_position: Decimal = Decimal("0"),
        **kwargs: Any,
    ) -> RiskCheckResult:
        if not self.enforce_on_all_intraday and position_type != "MIS":
            return RiskCheckResult(allowed=True)

        if current_time is None:
            return RiskCheckResult(allowed=True, metadata={"warning": "no_time_provided"})

        # Check if we're in square-off window
        current_hour = current_time.hour if hasattr(current_time, "hour") else 0
        current_minute = current_time.minute if hasattr(current_time, "minute") else 0

        # Minutes until square-off
        square_off_total_minutes = self._square_off_hour * 60 + self._square_off_minute
        current_total_minutes = current_hour * 60 + current_minute
        minutes_until = square_off_total_minutes - current_total_minutes

        if minutes_until <= 0:
            # Past square-off time - only allow closing orders
            is_closing = (
                (side == "SELL" and current_position > 0) or
                (side == "BUY" and current_position < 0)
            )
            if not is_closing:
                return RiskCheckResult(
                    allowed=False,
                    reason="mis_square_off_time_passed",
                    metadata={"current_time": f"{current_hour:02d}:{current_minute:02d}"},
                )
        elif minutes_until <= self.warning_minutes:
            # Warning period
            return RiskCheckResult(
                allowed=True,
                reason="mis_square_off_warning",
                metadata={
                    "minutes_until_square_off": minutes_until,
                    "square_off_time": self.square_off_time,
                },
            )

        return RiskCheckResult(allowed=True)


class CircuitBandGuard(BaseRiskGuard):
    """Circuit Band & Price Band Lock Guard.

    Prevents orders outside exchange circuit bands (upper/lower circuit limits)
    and price bands (dynamic price range for the day).
    """

    name = "circuit_band"

    def __init__(
        self,
        enforce_upper_circuit: bool = True,
        enforce_lower_circuit: bool = True,
        enforce_price_band: bool = True,
        price_band_buffer_pct: Decimal = Decimal("0.001"),  # 0.1% buffer
    ) -> None:
        """
        Args:
            enforce_upper_circuit: Reject orders above upper circuit
            enforce_lower_circuit: Reject orders below lower circuit
            enforce_price_band: Reject orders outside dynamic price band
            price_band_buffer_pct: Buffer inside price bands
        """
        self.enforce_upper_circuit = enforce_upper_circuit
        self.enforce_lower_circuit = enforce_lower_circuit
        self.enforce_price_band = enforce_price_band
        self.price_band_buffer_pct = price_band_buffer_pct

        # Static circuit limits (would be fetched from exchange in production)
        self._circuit_limits: dict[str, tuple[Decimal, Decimal]] = {}

    def set_circuit_limits(self, symbol: str, lower: Decimal, upper: Decimal) -> None:
        """Set circuit limits for a symbol."""
        self._circuit_limits[symbol] = (lower, upper)

    def check(
        self,
        instrument_id: InstrumentId,
        side: str,
        quantity: Decimal,
        price: Decimal,
        upper_circuit: Decimal | None = None,
        lower_circuit: Decimal | None = None,
        price_band_upper: Decimal | None = None,
        price_band_lower: Decimal | None = None,
        **kwargs: Any,
    ) -> RiskCheckResult:
        symbol = instrument_id.symbol

        # Get circuit limits (from args or stored)
        lower = lower_circuit or self._circuit_limits.get(symbol, (None, None))[0]
        upper = upper_circuit or self._circuit_limits.get(symbol, (None, None))[1]

        # Check upper circuit
        if self.enforce_upper_circuit and upper is not None and price > upper:
            return RiskCheckResult(
                allowed=False,
                reason="above_upper_circuit",
                metadata={"price": str(price), "upper_circuit": str(upper)},
            )

        # Check lower circuit
        if self.enforce_lower_circuit and lower is not None and price < lower:
            return RiskCheckResult(
                allowed=False,
                reason="below_lower_circuit",
                metadata={"price": str(price), "lower_circuit": str(lower)},
            )

        # Check dynamic price band
        if self.enforce_price_band and price_band_upper is not None and price_band_lower is not None:
            buffer = price * self.price_band_buffer_pct
            if price > price_band_upper - buffer:
                return RiskCheckResult(
                    allowed=False,
                    reason="above_price_band",
                    metadata={"price": str(price), "price_band_upper": str(price_band_upper)},
                )
            if price < price_band_lower + buffer:
                return RiskCheckResult(
                    allowed=False,
                    reason="below_price_band",
                    metadata={"price": str(price), "price_band_lower": str(price_band_lower)},
                )

        return RiskCheckResult(allowed=True)


class MaxPositionGuard(BaseRiskGuard):
    """Maximum Position Size Guard.

    Enforces maximum position limits per instrument and portfolio-level.
    """

    name = "max_position"

    def __init__(
        self,
        max_position_pct: Decimal = Decimal("0.10"),  # 10% of equity per position
        max_portfolio_risk_pct: Decimal = Decimal("0.05"),  # 5% total portfolio risk
        freeze_limit: int = 1800,
        lot_size: Decimal = Decimal("1"),
    ) -> None:
        self.max_position_pct = max_position_pct
        self.max_portfolio_risk_pct = max_portfolio_risk_pct
        self.freeze_limit = freeze_limit
        self.lot_size = lot_size

    def check(
        self,
        instrument_id: InstrumentId,
        side: str,
        quantity: Decimal,
        price: Decimal,
        equity: Decimal = Decimal("0"),
        current_position: Decimal = Decimal("0"),
        portfolio_risk: Decimal = Decimal("0"),
        **kwargs: Any,
    ) -> RiskCheckResult:
        capped = False
        reason = None
        adjusted_qty = quantity

        # Check freeze limit
        if quantity > self.freeze_limit:
            adjusted_qty = Decimal(str(self.freeze_limit))
            # Re-discretize to lot size
            lots = (adjusted_qty / self.lot_size).quantize(Decimal("1"), rounding="ROUND_DOWN")
            adjusted_qty = lots * self.lot_size
            capped = True
            reason = f"freeze_limit_{self.freeze_limit}"

        # Check max position notional
        if equity > 0:
            max_notional = equity * self.max_position_pct
            position_notional = adjusted_qty * price
            if position_notional > max_notional:
                adjusted_qty = (max_notional / price).quantize(Decimal("1"), rounding="ROUND_DOWN")
                lots = (adjusted_qty / self.lot_size).quantize(Decimal("1"), rounding="ROUND_DOWN")
                adjusted_qty = lots * self.lot_size
                capped = True
                reason = f"max_position_pct_{self.max_position_pct}"

        # Check portfolio risk
        if portfolio_risk > 0:
            max_portfolio_risk = equity * self.max_portfolio_risk_pct
            # Simplified: assume this order adds to portfolio risk proportionally
            if portfolio_risk > max_portfolio_risk:
                return RiskCheckResult(
                    allowed=False,
                    reason="portfolio_risk_exceeded",
                    metadata={
                        "current_portfolio_risk": str(portfolio_risk),
                        "max_portfolio_risk": str(max_portfolio_risk),
                    },
                )

        return RiskCheckResult(
            allowed=adjusted_qty > 0,
            adjusted_quantity=adjusted_qty if capped else None,
            reason=reason,
            metadata={"capped": capped},
        )


class DrawdownHaltGuard(BaseRiskGuard):
    """Drawdown Halt Guard.

    Halts all new order placement when portfolio drawdown exceeds threshold.
    """

    name = "drawdown_halt"

    def __init__(
        self,
        max_drawdown_pct: Decimal = Decimal("0.10"),  # 10% max drawdown
        warning_drawdown_pct: Decimal = Decimal("0.05"),  # 5% warning
        peak_equity: Decimal | None = None,
    ) -> None:
        self.max_drawdown_pct = max_drawdown_pct
        self.warning_drawdown_pct = warning_drawdown_pct
        self._peak_equity = peak_equity or Decimal("0")

    def update_peak_equity(self, equity: Decimal) -> None:
        """Update peak equity for drawdown calculation."""
        if equity > self._peak_equity:
            self._peak_equity = equity

    def check(
        self,
        instrument_id: InstrumentId,
        side: str,
        quantity: Decimal,
        price: Decimal,
        current_equity: Decimal = Decimal("0"),
        **kwargs: Any,
    ) -> RiskCheckResult:
        if self._peak_equity <= 0 or current_equity <= 0:
            return RiskCheckResult(allowed=True, metadata={"warning": "no_equity_data"})

        drawdown = (self._peak_equity - current_equity) / self._peak_equity

        if drawdown >= self.max_drawdown_pct:
            return RiskCheckResult(
                allowed=False,
                reason="max_drawdown_exceeded",
                metadata={
                    "drawdown": str(drawdown),
                    "max_drawdown": str(self.max_drawdown_pct),
                    "peak_equity": str(self._peak_equity),
                    "current_equity": str(current_equity),
                },
            )

        if drawdown >= self.warning_drawdown_pct:
            return RiskCheckResult(
                allowed=True,
                reason="drawdown_warning",
                metadata={
                    "drawdown": str(drawdown),
                    "warning_threshold": str(self.warning_drawdown_pct),
                },
            )

        return RiskCheckResult(allowed=True)