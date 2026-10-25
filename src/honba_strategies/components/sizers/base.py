"""Base Position Sizing Architecture.

Defines the core abstractions for dynamic position sizing: SizingContext, SizingResult,
and the BasePositionSizer abstract base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from honba.entities.instrument import InstrumentId


@dataclass
class SizingContext:
    """Context captured for position sizing calculations.

    Contains account equity, cash balance, margin requirements, and active
    portfolio positions needed for risk-aware sizing decisions.
    """

    equity: Decimal
    cash_balance: Decimal
    margin_used: Decimal
    available_margin: Decimal
    positions: dict[str, Decimal] = field(default_factory=dict)
    instrument_id: InstrumentId | None = None
    current_price: Decimal | None = None
    atr: Decimal | None = None  # Current ATR for volatility-based sizing

    @property
    def free_equity(self) -> Decimal:
        """Equity available for new positions after margin."""
        return self.equity - self.margin_used

    @property
    def total_portfolio_value(self) -> Decimal:
        """Total portfolio value including positions."""
        return self.equity


@dataclass
class PositionSizingResult:
    """Result of a position sizing calculation.

    Attributes:
        quantity: Calculated position size in lots/contracts (discretized to lot size)
        notional: Cash notional value of the position
        risk_at_stake: Maximum risk amount if stop-loss is hit
        capped_by_limit: Whether the result was capped by any limits (freeze, max position, etc.)
        capping_reason: Description of which limit was hit, if any
        stop_distance: Distance from entry to stop-loss
        lot_size: Exchange lot size used for discretization
    """

    quantity: Decimal
    notional: Decimal
    risk_at_stake: Decimal
    capped_by_limit: bool = False
    capping_reason: str | None = None
    stop_distance: Decimal | None = None
    lot_size: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("quantity must be non-negative")
        if self.notional < 0:
            raise ValueError("notional must be non-negative")
        if self.risk_at_stake < 0:
            raise ValueError("risk_at_stake must be non-negative")


@dataclass
class Signal:
    """Trading signal with direction, entry price, stop-loss, and volatility.

    This is the standard contract between signal generators and position sizers.
    """

    direction: int  # +1 for long, -1 for short, 0 for flat
    entry_price: Decimal
    stop_loss: Decimal | None = None
    volatility_atr: Decimal | None = None
    confidence: Decimal = Decimal("1.0")  # Signal confidence [0, 1]
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.direction not in (-1, 0, 1):
            raise ValueError("direction must be -1, 0, or 1")
        if self.entry_price <= 0:
            raise ValueError("entry_price must be positive")
        if self.stop_loss is not None and self.stop_loss <= 0:
            raise ValueError("stop_loss must be positive")
        if self.volatility_atr is not None and self.volatility_atr <= 0:
            raise ValueError("volatility_atr must be positive")
        if not (Decimal("0") <= self.confidence <= Decimal("1")):
            raise ValueError("confidence must be in [0, 1]")

    @property
    def stop_distance(self) -> Decimal | None:
        """Absolute distance from entry to stop-loss."""
        if self.stop_loss is None:
            return None
        if self.direction > 0:
            return self.entry_price - self.stop_loss
        elif self.direction < 0:
            return self.stop_loss - self.entry_price
        return None

    @property
    def is_valid(self) -> bool:
        """Check if signal has actionable direction and valid stop distance."""
        return self.direction != 0 and self.stop_distance is not None and self.stop_distance > 0


class BasePositionSizer(ABC):
    """Abstract base class for all position sizing engines.

    Sizers implement the core sizing logic: given a signal, account equity,
    and risk parameters, compute the exact position size to take.
    """

    name: str = "base_sizer"

    @abstractmethod
    def calculate_size(
        self,
        signal: Signal,
        context: SizingContext,
        **kwargs: Any,
    ) -> PositionSizingResult:
        """Calculate position size for a given signal and context.

        Args:
            signal: Trading signal with direction, entry, stop-loss, and ATR
            context: Account context with equity, margin, positions
            **kwargs: Additional sizer-specific parameters

        Returns:
            PositionSizingResult with quantity, notional, risk, and capping info
        """
        pass

    def _discretize_quantity(
        self,
        quantity: Decimal,
        lot_size: Decimal,
        freeze_limit: int | None = None,
    ) -> tuple[Decimal, bool, str | None]:
        """Discretize quantity to exchange lot size and apply freeze limit.

        Args:
            quantity: Raw calculated quantity
            lot_size: Exchange lot size (e.g., 25 for NIFTY, 15 for BANKNIFTY)
            freeze_limit: Optional exchange freeze limit (e.g., 1800 for NIFTY)

        Returns:
            Tuple of (discretized_quantity, capped, capping_reason)
        """
        if lot_size <= 0:
            raise ValueError("lot_size must be positive")

        # Round down to nearest lot size multiple
        lots = (quantity / lot_size).quantize(Decimal("1"), rounding="ROUND_DOWN")
        discretized = lots * lot_size

        capped = False
        reason = None

        # Apply freeze limit
        if freeze_limit is not None and discretized > freeze_limit:
            discretized = Decimal(str(freeze_limit))
            # Re-discretize to lot size
            lots = (discretized / lot_size).quantize(Decimal("1"), rounding="ROUND_DOWN")
            discretized = lots * lot_size
            capped = True
            reason = f"exchange_freeze_limit_{freeze_limit}"

        return discretized, capped, reason

    def _apply_max_position_cap(
        self,
        quantity: Decimal,
        price: Decimal,
        max_notional: Decimal,
    ) -> tuple[Decimal, bool, str | None]:
        """Apply maximum position notional cap.

        Args:
            quantity: Current quantity
            price: Entry price
            max_notional: Maximum allowed notional value

        Returns:
            Tuple of (capped_quantity, capped, capping_reason)
        """
        notional = quantity * price
        if notional <= max_notional:
            return quantity, False, None

        capped_qty = (max_notional / price).quantize(Decimal("1"), rounding="ROUND_DOWN")
        return capped_qty, True, f"max_position_notional_{max_notional}"

    def _apply_max_risk_cap(
        self,
        quantity: Decimal,
        stop_distance: Decimal,
        max_risk: Decimal,
    ) -> tuple[Decimal, bool, str | None]:
        """Apply maximum risk per trade cap.

        Args:
            quantity: Current quantity
            stop_distance: Distance from entry to stop
            max_risk: Maximum allowed risk amount

        Returns:
            Tuple of (capped_quantity, capped, capping_reason)
        """
        risk = quantity * stop_distance
        if risk <= max_risk:
            return quantity, False, None

        capped_qty = (max_risk / stop_distance).quantize(Decimal("1"), rounding="ROUND_DOWN")
        return capped_qty, True, f"max_risk_per_trade_{max_risk}"