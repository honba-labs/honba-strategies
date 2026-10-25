"""Tests for Equal Risk Sizer catalog entry."""

from decimal import Decimal

import pytest

from honba_strategies.components.sizers import EqualRiskSizer
from honba_strategies.core.registry import get_strategy, list_strategies


class TestEqualRiskSizer:
    """Test Equal Risk Contribution Sizer catalog entry."""

    def test_strategy_import(self):
        """Test that the sizer can be imported from catalog."""
        from catalog.size.equal_risk.strategy import EqualRiskSizer as CatalogEqualRiskSizer
        assert CatalogEqualRiskSizer is EqualRiskSizer

    def test_registry_integration(self):
        """Test sizer is registered in SDK registry."""
        strategies = list_strategies(category="size")
        names = [s["name"] for s in strategies]
        assert "equal_risk" in names

        sizer_class = get_strategy("equal_risk")
        assert sizer_class is not None
        assert sizer_class.__name__ == "EqualRiskSizer"

    def test_config_defaults(self):
        """Test config default values."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )
        assert sizer.total_risk_pct == Decimal("0.05")
        assert sizer.max_position_notional == Decimal("500000")
        assert sizer.use_correlation is True

    def test_single_signal_mode(self):
        """Test ERC with single signal (uses full budget)."""
        sizer = EqualRiskSizer(
            total_risk_pct=Decimal("0.05"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
            use_correlation=False,
        )

        from honba.entities.instrument import InstrumentId

        from honba_strategies.components.sizers.base import Signal, SizingContext

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("23700"),
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context, all_signals=[signal])
        # Total risk = 1,000,000 * 0.05 = 50,000
        # Single signal gets full 50,000
        # Q = 50,000 / 300 = 166.67 -> 150 lots (25 * 6)
        assert result.quantity == Decimal("150")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])