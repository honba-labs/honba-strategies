"""Fixed Fractional Position Sizer.

Risks a fixed percentage of account equity per trade, divided by the stop-loss distance.
This is the classic "risk 1% of equity per trade" sizing methodology.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from honba_strategies.components.sizers.base import BasePositionSizer, PositionSizingResult, Signal, SizingContext


class FixedFractionalSizer(BasePositionSizer):
    """Fixed Fractional Sizing: Risk % of equity per trade vs stop-loss distance.

    Formula:
        Q = floor(Equity * RiskPct / |P_entry - P_stop| / LotSize) * LotSize

    Where:
        - Equity: Total account equity
        - RiskPct: Fraction of equity to risk per trade (e.g., 0.01 = 1%)
        - P_entry - P_stop: Stop-loss distance per share/contract
        - LotSize: Exchange lot size for discretization
    """

    name = "fixed_fractional"

    def __init__(
        self,
        risk_pct: Decimal = Decimal("0.01"),
        max_position_notional: Decimal | None = None,
        max_risk_per_trade: Decimal | None = None,
        lot_size: Decimal = Decimal("1"),
        freeze_limit: int | None = None,
        fallback_stop_atr_mult: Decimal = Decimal("2.0"),
    ) -> None:
        """
        Args:
            risk_pct: Percentage of equity to risk per trade (default 1%)
            max_position_notional: Hard cap on position notional value
            max_risk_per_trade: Hard cap on absolute risk amount per trade
            lot_size: Exchange lot size for discretization
            freeze_limit: Exchange single-order freeze limit
            fallback_stop_atr_mult: ATR multiplier for fallback stop when signal lacks explicit stop
        """
        if not (Decimal("0") < risk_pct <= Decimal("0.1")):
            raise ValueError("risk_pct must be in (0, 0.1]")
        if max_position_notional is not None and max_position_notional <= 0:
            raise ValueError("max_position_notional must be positive")
        if max_risk_per_trade is not None and max_risk_per_trade <= 0:
            raise ValueError("max_risk_per_trade must be positive")
        if lot_size <= 0:
            raise ValueError("lot_size must be positive")

        self.risk_pct = risk_pct
        self.max_position_notional = max_position_notional
        self.max_risk_per_trade = max_risk_per_trade
        self.lot_size = lot_size
        self.freeze_limit = freeze_limit
        self.fallback_stop_atr_mult = fallback_stop_atr_mult

    def calculate_size(
        self,
        signal: Signal,
        context: SizingContext,
        **kwargs: Any,
    ) -> PositionSizingResult:
        """Calculate fixed fractional position size."""
        if not signal.is_valid:
            # Try to use fallback stop based on ATR
            if signal.volatility_atr is not None:
                fallback_stop = signal.volatility_atr * self.fallback_stop_atr_mult
                if signal.direction > 0:
                    signal.stop_loss = signal.entry_price - fallback_stop
                else:
                    signal.stop_loss = signal.entry_price + fallback_stop
            else:
                # No valid stop distance - return zero size
                return PositionSizingResult(
                    quantity=Decimal("0"),
                    notional=Decimal("0"),
                    risk_at_stake=Decimal("0"),
                    capped_by_limit=False,
                    capping_reason="no_valid_stop_distance",
                    stop_distance=None,
                    lot_size=self.lot_size,
                )

        stop_distance: Decimal | None = signal.stop_distance
        if stop_distance is None or stop_distance <= 0:
            return PositionSizingResult(
                quantity=Decimal("0"),
                notional=Decimal("0"),
                risk_at_stake=Decimal("0"),
                capped_by_limit=False,
                capping_reason="invalid_stop_distance",
                stop_distance=stop_distance,
                lot_size=self.lot_size,
            )

        # Core fixed fractional formula
        equity = context.equity
        risk_amount = equity * self.risk_pct
        raw_quantity = risk_amount / stop_distance

        # Discretize to lot size
        quantity, capped, reason = self._discretize_quantity(raw_quantity, self.lot_size, self.freeze_limit)

        # Apply max position notional cap
        if self.max_position_notional is not None and quantity > 0:
            price = context.current_price or signal.entry_price
            quantity, cap2, reason2 = self._apply_max_position_cap(quantity, price, self.max_position_notional)
            if cap2:
                capped = True
                reason = reason2

        # Apply max risk per trade cap
        if self.max_risk_per_trade is not None and quantity > 0:
            quantity, cap3, reason3 = self._apply_max_risk_cap(quantity, stop_distance, self.max_risk_per_trade)
            if cap3:
                capped = True
                reason = reason3

        notional = quantity * (context.current_price or signal.entry_price)
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