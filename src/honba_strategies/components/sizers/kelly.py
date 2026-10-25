"""Kelly Criterion & Optimal-f Position Sizer.

Computes optimal capital allocation fraction from win-rate and win/loss ratio.
Implements fractional Kelly damping (Half-Kelly, Quarter-Kelly) for drawdown control.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from honba_strategies.components.sizers.base import BasePositionSizer, PositionSizingResult, Signal, SizingContext


class KellySizer(BasePositionSizer):
    """Kelly Criterion & Optimal-f Sizer.

    Kelly formula: f* = p - (1 - p) / b
    Where:
        - p = win probability
        - b = win/loss ratio (average win / average loss)

    Implements fractional Kelly (e.g., 0.5 * f* for Half-Kelly) to minimize drawdown risk.
    """

    name = "kelly_criterion"

    def __init__(
        self,
        win_rate: Decimal = Decimal("0.55"),
        win_loss_ratio: Decimal = Decimal("1.5"),
        kelly_fraction: Decimal = Decimal("0.5"),  # Half-Kelly by default
        max_position_notional: Decimal | None = None,
        max_risk_per_trade: Decimal | None = None,
        lot_size: Decimal = Decimal("1"),
        freeze_limit: int | None = None,
        fallback_stop_atr_mult: Decimal = Decimal("2.0"),
        min_kelly_fraction: Decimal = Decimal("0.0"),
        max_kelly_fraction: Decimal = Decimal("1.0"),
    ) -> None:
        """
        Args:
            win_rate: Historical win probability (0 to 1)
            win_loss_ratio: Average win / average loss ratio
            kelly_fraction: Fraction of full Kelly to use (0.5 = Half-Kelly, 0.25 = Quarter-Kelly)
            max_position_notional: Hard cap on position notional value
            max_risk_per_trade: Hard cap on absolute risk amount per trade
            lot_size: Exchange lot size for discretization
            freeze_limit: Exchange single-order freeze limit
            fallback_stop_atr_mult: ATR multiplier for fallback stop
            min_kelly_fraction: Minimum allowed Kelly fraction (floor)
            max_kelly_fraction: Maximum allowed Kelly fraction (cap)
        """
        if not (Decimal("0") < win_rate < Decimal("1")):
            raise ValueError("win_rate must be in (0, 1)")
        if win_loss_ratio <= 0:
            raise ValueError("win_loss_ratio must be positive")
        if not (Decimal("0") <= kelly_fraction <= Decimal("1")):
            raise ValueError("kelly_fraction must be in [0, 1]")
        if max_position_notional is not None and max_position_notional <= 0:
            raise ValueError("max_position_notional must be positive")
        if max_risk_per_trade is not None and max_risk_per_trade <= 0:
            raise ValueError("max_risk_per_trade must be positive")
        if lot_size <= 0:
            raise ValueError("lot_size must be positive")

        self.win_rate = win_rate
        self.win_loss_ratio = win_loss_ratio
        self.kelly_fraction = kelly_fraction
        self.max_position_notional = max_position_notional
        self.max_risk_per_trade = max_risk_per_trade
        self.lot_size = lot_size
        self.freeze_limit = freeze_limit
        self.fallback_stop_atr_mult = fallback_stop_atr_mult
        self.min_kelly_fraction = min_kelly_fraction
        self.max_kelly_fraction = max_kelly_fraction

    def _compute_kelly_fraction(self) -> Decimal:
        """Compute the Kelly optimal fraction: f* = p - (1-p)/b."""
        p = self.win_rate
        b = self.win_loss_ratio
        kelly = p - (Decimal("1") - p) / b

        # Clamp to bounds
        if kelly < self.min_kelly_fraction:
            kelly = self.min_kelly_fraction
        if kelly > self.max_kelly_fraction:
            kelly = self.max_kelly_fraction

        return kelly

    def calculate_size(
        self,
        signal: Signal,
        context: SizingContext,
        **kwargs: Any,
    ) -> PositionSizingResult:
        """Calculate Kelly-based position size."""
        # Allow runtime override of win_rate and win_loss_ratio from signal metadata
        win_rate = signal.metadata.get("win_rate", self.win_rate)
        win_loss_ratio = signal.metadata.get("win_loss_ratio", self.win_loss_ratio)

        if isinstance(win_rate, (int, float, str)):
            win_rate = Decimal(str(win_rate))
        if isinstance(win_loss_ratio, (int, float, str)):
            win_loss_ratio = Decimal(str(win_loss_ratio))

        # Compute Kelly fraction
        p = win_rate
        b = win_loss_ratio
        if b <= 0 or p <= 0 or p >= 1:
            return PositionSizingResult(
                quantity=Decimal("0"),
                notional=Decimal("0"),
                risk_at_stake=Decimal("0"),
                capped_by_limit=False,
                capping_reason="invalid_kelly_params",
                stop_distance=None,
                lot_size=self.lot_size,
            )

        kelly_full = p - (Decimal("1") - p) / b

        # Apply fractional Kelly damping
        kelly_fraction = kelly_full * self.kelly_fraction

        # Clamp
        if kelly_fraction < self.min_kelly_fraction:
            kelly_fraction = self.min_kelly_fraction
        if kelly_fraction > self.max_kelly_fraction:
            kelly_fraction = self.max_kelly_fraction

        if kelly_fraction <= 0:
            return PositionSizingResult(
                quantity=Decimal("0"),
                notional=Decimal("0"),
                risk_at_stake=Decimal("0"),
                capped_by_limit=False,
                capping_reason="non_positive_kelly_fraction",
                stop_distance=None,
                lot_size=self.lot_size,
            )

        # Determine stop distance
        stop_distance = signal.stop_distance
        if stop_distance is None or stop_distance <= 0:
            if signal.volatility_atr is not None:
                stop_distance = signal.volatility_atr * self.fallback_stop_atr_mult
            else:
                return PositionSizingResult(
                    quantity=Decimal("0"),
                    notional=Decimal("0"),
                    risk_at_stake=Decimal("0"),
                    capped_by_limit=False,
                    capping_reason="no_valid_stop_distance",
                    stop_distance=None,
                    lot_size=self.lot_size,
                )

        # Kelly position size: f* * equity / stop_distance
        equity = context.equity
        risk_amount = equity * kelly_fraction
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