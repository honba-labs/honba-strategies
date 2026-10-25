"""Fixed Cash Notional Position Sizer.

Targets a fixed cash allocation per position, discretized to exchange lot sizes.
Simple and predictable sizing for capital allocation frameworks.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from honba_strategies.components.sizers.base import (
    BasePositionSizer,
    PositionSizingResult,
    Signal,
    SizingContext,
)


class FixedNotionalSizer(BasePositionSizer):
    """Fixed Notional Sizer: Target INR/USD fixed cash allocation per trade.

    Formula:
        Q = floor(Notional / (P_entry * LotSize)) * LotSize

    Simple, predictable sizing that allocates a fixed cash amount per position.
    """

    name = "fixed_notional"

    def __init__(
        self,
        target_notional: Decimal = Decimal("100000"),
        max_position_notional: Decimal | None = None,
        lot_size: Decimal = Decimal("1"),
        freeze_limit: int | None = None,
    ) -> None:
        """
        Args:
            target_notional: Target cash notional per position (e.g., ₹100,000)
            max_position_notional: Hard cap on position notional (can be same as target)
            lot_size: Exchange lot size for discretization
            freeze_limit: Exchange single-order freeze limit
        """
        if target_notional <= 0:
            raise ValueError("target_notional must be positive")
        if max_position_notional is not None and max_position_notional <= 0:
            raise ValueError("max_position_notional must be positive")
        if lot_size <= 0:
            raise ValueError("lot_size must be positive")

        self.target_notional = target_notional
        self.max_position_notional = max_position_notional or target_notional
        self.lot_size = lot_size
        self.freeze_limit = freeze_limit

    def calculate_size(
        self,
        signal: Signal,
        context: SizingContext,
        **kwargs: Any,
    ) -> PositionSizingResult:
        """Calculate fixed notional position size."""
        if signal.direction == 0:
            return PositionSizingResult(
                quantity=Decimal("0"),
                notional=Decimal("0"),
                risk_at_stake=Decimal("0"),
                capped_by_limit=False,
                capping_reason="flat_signal",
                stop_distance=None,
                lot_size=self.lot_size,
            )

        price = context.current_price or signal.entry_price
        if price <= 0:
            return PositionSizingResult(
                quantity=Decimal("0"),
                notional=Decimal("0"),
                risk_at_stake=Decimal("0"),
                capped_by_limit=False,
                capping_reason="invalid_price",
                stop_distance=None,
                lot_size=self.lot_size,
            )

        # Core formula: Q = Notional / Price, then discretize to lot size
        raw_quantity = self.target_notional / price

        # Discretize to lot size
        quantity, capped, reason = self._discretize_quantity(raw_quantity, self.lot_size, self.freeze_limit)

        # Apply max position notional cap
        if quantity > 0:
            quantity, cap2, reason2 = self._apply_max_position_cap(quantity, price, self.max_position_notional)
            if cap2:
                capped = True
                reason = reason2

        notional = quantity * price

        # Calculate risk at stake if stop is available
        risk_at_stake = Decimal("0")
        stop_distance = signal.stop_distance
        if stop_distance is not None and stop_distance > 0:
            risk_at_stake = quantity * stop_distance

        return PositionSizingResult(
            quantity=quantity,
            notional=notional,
            risk_at_stake=risk_at_stake,
            capped_by_limit=capped,
            capping_reason=reason,
            stop_distance=stop_distance,
            lot_size=self.lot_size,
        )