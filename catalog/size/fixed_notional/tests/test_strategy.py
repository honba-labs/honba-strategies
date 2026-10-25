"""Tests for Fixed Notional Sizer catalog entry."""

from decimal import Decimal

import pytest

from honba_strategies.components.sizers import FixedNotionalSizer
from honba_strategies.core.registry import get_strategy, list_strategies


class TestFixedNotionalSizer:
    """Test Fixed Notional Sizer catalog entry."""

    def test_strategy_import(self):
        """Test that the sizer can be imported from catalog."""
        from catalog.size.fixed_notional.strategy import (
            FixedNotionalSizer as CatalogFixedNotionalSizer,
        )
        assert CatalogFixedNotionalSizer is FixedNotionalSizer

    def test_registry_integration(self):
        """Test sizer is registered in SDK registry."""
        strategies = list_strategies(category="size")
        names = [s["name"] for s in strategies]
        assert "fixed_notional" in names

        sizer_class = get_strategy("fixed_notional")
        assert sizer_class is not None
        assert sizer_class.__name__ == "FixedNotionalSizer"

    def test_config_defaults(self):
        """Test config default values."""
        sizer = FixedNotionalSizer(
            target_notional=Decimal("100000"),
            max_position_notional=Decimal("100000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )
        assert sizer.target_notional == Decimal("100000")
        assert sizer.max_position_notional == Decimal("100000")

    def test_basic_notional_sizing(self):
        """Test basic fixed notional sizing."""
        from honba.entities.instrument import InstrumentId

        from honba_strategies.components.sizers.base import Signal, SizingContext

        sizer = FixedNotionalSizer(
            target_notional=Decimal("600000"),
            max_position_notional=Decimal("600000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(direction=1, entry_price=Decimal("24000"))
        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("0"),
            available_margin=Decimal("800000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
        )

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("25")
        assert result.notional == Decimal("600000")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])