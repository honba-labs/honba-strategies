"""Tests for Fixed Fractional Sizer catalog entry."""

from decimal import Decimal

import pytest

from honba_strategies.components.sizers import FixedFractionalSizer
from honba_strategies.core.registry import get_strategy, list_strategies


class TestFixedFractionalSizer:
    """Test Fixed Fractional Sizer catalog entry."""

    def test_strategy_import(self):
        """Test that the sizer can be imported from catalog."""
        from catalog.size.fixed_fractional.strategy import (
            FixedFractionalSizer as CatalogFixedFractionalSizer,
        )
        assert CatalogFixedFractionalSizer is FixedFractionalSizer

    def test_registry_integration(self):
        """Test sizer is registered in SDK registry."""
        strategies = list_strategies(category="size")
        names = [s["name"] for s in strategies]
        assert "fixed_fractional" in names

        sizer_class = get_strategy("fixed_fractional")
        assert sizer_class is not None
        assert sizer_class.__name__ == "FixedFractionalSizer"

    def test_config_defaults(self):
        """Test config default values."""
        sizer = FixedFractionalSizer(
            risk_pct=Decimal("0.01"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )
        assert sizer.risk_pct == Decimal("0.01")
        assert sizer.max_position_notional == Decimal("500000")

    def test_basic_sizing_with_explicit_stop(self):
        """Test sizing with explicit stop-loss in signal."""
        from honba.entities.instrument import InstrumentId

        from honba_strategies.components.sizers.base import Signal, SizingContext

        sizer = FixedFractionalSizer(
            risk_pct=Decimal("0.01"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            stop_loss=Decimal("23700"),
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("200000"),
            available_margin=Decimal("600000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("25")
        assert result.notional == Decimal("600000")
        assert result.risk_at_stake == Decimal("7500")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])