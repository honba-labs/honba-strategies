"""Equal Risk Contribution Position Sizer.

Multi-signal simultaneous sizer that allocates risk budget equally across K
active candidate signals, with cross-asset correlation adjustments.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from honba_strategies.components.sizers.base import BasePositionSizer, PositionSizingResult, Signal, SizingContext


class EqualRiskSizer(BasePositionSizer):
    """Equal Risk Contribution (ERC) / Risk Parity Sizer.

    Allocates the total risk budget equally across all active signals,
    adjusting for cross-asset correlations using the covariance matrix.

    For K signals with equal risk budget:
        Each signal gets risk_budget = TotalRisk / K

    With correlation adjustment:
        w = (1/N) * Σ⁻¹ * 1  (scaled to target risk)
    """

    name = "equal_risk"

    def __init__(
        self,
        total_risk_pct: Decimal = Decimal("0.05"),  # Total portfolio risk budget (5%)
        max_position_notional: Decimal | None = None,
        lot_size: Decimal = Decimal("1"),
        freeze_limit: int | None = None,
        fallback_stop_atr_mult: Decimal = Decimal("2.0"),
        use_correlation: bool = True,
        min_correlation: Decimal = Decimal("-0.5"),
        max_correlation: Decimal = Decimal("0.9"),
    ) -> None:
        """
        Args:
            total_risk_pct: Total portfolio risk budget as fraction of equity
            max_position_notional: Hard cap on individual position notional
            lot_size: Exchange lot size for discretization
            freeze_limit: Exchange single-order freeze limit
            fallback_stop_atr_mult: ATR multiplier for fallback stop
            use_correlation: Whether to use correlation matrix for adjustment
            min_correlation: Floor for correlation matrix elements
            max_correlation: Cap for correlation matrix elements
        """
        if not (Decimal("0") < total_risk_pct <= Decimal("0.2")):
            raise ValueError("total_risk_pct must be in (0, 0.2]")
        if max_position_notional is not None and max_position_notional <= 0:
            raise ValueError("max_position_notional must be positive")
        if lot_size <= 0:
            raise ValueError("lot_size must be positive")
        if not (Decimal("-1") <= min_correlation < max_correlation <= Decimal("1")):
            raise ValueError("correlation bounds must be in [-1, 1] with min < max")

        self.total_risk_pct = total_risk_pct
        self.max_position_notional = max_position_notional
        self.lot_size = lot_size
        self.freeze_limit = freeze_limit
        self.fallback_stop_atr_mult = fallback_stop_atr_mult
        self.use_correlation = use_correlation
        self.min_correlation = min_correlation
        self.max_correlation = max_correlation

    def calculate_size(
        self,
        signal: Signal,
        context: SizingContext,
        all_signals: list[Signal] | None = None,
        correlation_matrix: list[list[Decimal]] | None = None,
        **kwargs: Any,
    ) -> PositionSizingResult:
        """Calculate equal risk position size for one signal in a multi-signal portfolio.

        Args:
            signal: The signal to size for
            context: Account context
            all_signals: List of all active signals (for ERC across K signals)
            correlation_matrix: KxK correlation matrix for cross-asset adjustment
            **kwargs: Additional parameters
        """
        if not signal.is_valid:
            if signal.volatility_atr is not None:
                fallback_stop = signal.volatility_atr * self.fallback_stop_atr_mult
                if signal.direction > 0:
                    signal.stop_loss = signal.entry_price - fallback_stop
                else:
                    signal.stop_loss = signal.entry_price + fallback_stop
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

        equity = context.equity
        total_risk_budget = equity * self.total_risk_pct

        # Determine number of active signals
        if all_signals is not None:
            active_signals = [s for s in all_signals if s.is_valid and s.direction != 0]
            k = len(active_signals)
        else:
            # Single signal mode - use full budget
            k = 1

        if k == 0:
            return PositionSizingResult(
                quantity=Decimal("0"),
                notional=Decimal("0"),
                risk_at_stake=Decimal("0"),
                capped_by_limit=False,
                capping_reason="no_active_signals",
                stop_distance=stop_distance,
                lot_size=self.lot_size,
            )

        # Risk budget per signal
        if self.use_correlation and correlation_matrix is not None and k > 1:
            # Use correlation-adjusted risk budget
            risk_per_signal = self._compute_erc_risk_budget(
                total_risk_budget, k, correlation_matrix, signal, all_signals
            )
        else:
            # Equal risk budget per signal
            risk_per_signal = total_risk_budget / Decimal(str(k))

        # Position size from risk budget
        raw_quantity = risk_per_signal / stop_distance

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

    def _compute_erc_risk_budget(
        self,
        total_risk: Decimal,
        k: int,
        corr_matrix: list[list[Decimal]],
        target_signal: Signal,
        all_signals: list[Signal] | None,
    ) -> Decimal:
        """Compute ERC risk budget using correlation matrix.

        Simplified ERC: w = Σ⁻¹ * 1 / (1ᵀ * Σ⁻¹ * 1) * total_risk
        For equal risk contribution, we want wᵀ * Σ * w = total_risk² with equal RC.
        """
        try:
            # Simple approach: adjust equal budget by average correlation
            # Average off-diagonal correlation
            n = len(corr_matrix)
            if n != k:
                return total_risk / Decimal(str(k))

            sum_corr = Decimal("0")
            count = 0
            for i in range(n):
                for j in range(n):
                    if i != j:
                        c = corr_matrix[i][j]
                        # Clamp correlation
                        if c < self.min_correlation:
                            c = self.min_correlation
                        elif c > self.max_correlation:
                            c = self.max_correlation
                        sum_corr += c
                        count += 1

            if count == 0:
                return total_risk / Decimal(str(k))

            avg_corr = sum_corr / Decimal(str(count))

            # Diversification ratio adjustment
            # When assets are correlated, effective N is smaller
            # div_ratio = sqrt(k) / sqrt(1 + (k-1)*avg_corr)
            if avg_corr >= Decimal("1"):
                div_ratio = Decimal("1")
            else:
                div_ratio = (Decimal(str(k)) ** Decimal("0.5")) / ((Decimal("1") + Decimal(str(k - 1)) * avg_corr) ** Decimal("0.5"))

            # Adjust risk budget by diversification ratio
            return (total_risk / Decimal(str(k))) * div_ratio

        except Exception:
            return total_risk / Decimal(str(k))