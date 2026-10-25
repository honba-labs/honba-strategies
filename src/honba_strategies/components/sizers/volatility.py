"""ATR Volatility-Targeted Position Sizer.

Inverse volatility allocation based on Average True Range (ATR). Sizes positions
so that each position contributes a target amount of portfolio volatility.
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


class AtrVolatilitySizer(BasePositionSizer):
    """ATR Volatility-Targeted Sizer.

    Two modes of operation:
    1. Inverse Volatility Sizing: Size inversely proportional to ATR
       Q = floor(Equity * TargetRisk / (ATR * ATRMult) / LotSize) * LotSize
    2. Volatility Targeting: Scale position sizes to target portfolio volatility
       (e.g., 15% annualized volatility)
    """

    name = "atr_volatility"

    def __init__(
        self,
        target_risk_pct: Decimal = Decimal("0.015"),
        atr_multiplier: Decimal = Decimal("2.0"),
        max_position_notional: Decimal | None = None,
        lot_size: Decimal = Decimal("1"),
        freeze_limit: int | None = None,
        # Volatility targeting mode
        target_annual_vol: Decimal | None = None,  # e.g., 0.15 for 15%
        trading_days: int = 252,
    ) -> None:
        """
        Args:
            target_risk_pct: Target risk as fraction of equity (used in inverse vol mode)
            atr_multiplier: Multiplier applied to ATR for stop distance (default 2.0)
            max_position_notional: Hard cap on position notional value
            lot_size: Exchange lot size for discretization
            freeze_limit: Exchange single-order freeze limit
            target_annual_vol: If set, enables volatility targeting mode (annualized)
            trading_days: Trading days per year for annualization
        """
        if not (Decimal("0") < target_risk_pct <= Decimal("0.1")):
            raise ValueError("target_risk_pct must be in (0, 0.1]")
        if atr_multiplier <= 0:
            raise ValueError("atr_multiplier must be positive")
        if max_position_notional is not None and max_position_notional <= 0:
            raise ValueError("max_position_notional must be positive")
        if lot_size <= 0:
            raise ValueError("lot_size must be positive")
        if target_annual_vol is not None and not (Decimal("0") < target_annual_vol <= Decimal("1")):
            raise ValueError("target_annual_vol must be in (0, 1]")

        self.target_risk_pct = target_risk_pct
        self.atr_multiplier = atr_multiplier
        self.max_position_notional = max_position_notional
        self.lot_size = lot_size
        self.freeze_limit = freeze_limit
        self.target_annual_vol = target_annual_vol
        self.trading_days = trading_days

    def calculate_size(
        self,
        signal: Signal,
        context: SizingContext,
        **kwargs: Any,
    ) -> PositionSizingResult:
        """Calculate ATR-based position size."""
        # Get ATR from signal or context
        atr = signal.volatility_atr or context.atr
        if atr is None or atr <= 0:
            return PositionSizingResult(
                quantity=Decimal("0"),
                notional=Decimal("0"),
                risk_at_stake=Decimal("0"),
                capped_by_limit=False,
                capping_reason="no_atr_available",
                stop_distance=None,
                lot_size=self.lot_size,
            )

        stop_distance = atr * self.atr_multiplier
        equity = context.equity

        if self.target_annual_vol is not None:
            # Volatility targeting mode: scale to target annual volatility
            # Daily vol target = annual_vol / sqrt(trading_days)
            daily_vol_target = self.target_annual_vol / Decimal(str(self.trading_days)) ** Decimal("0.5")
            # Position vol = qty * price * daily_vol / equity
            # qty = daily_vol_target * equity / (price * atr)
            price = context.current_price or signal.entry_price
            raw_quantity = (daily_vol_target * equity) / (price * atr)
        else:
            # Inverse volatility sizing mode
            risk_amount = equity * self.target_risk_pct
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