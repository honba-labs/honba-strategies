"""Tests for ATR Volatility Sizer catalog entry."""

from decimal import Decimal

import pytest

from honba_strategies.components.sizers import AtrVolatilitySizer
from honba_strategies.core.registry import get_strategy, list_strategies


class TestAtrVolatilitySizer:
    """Test ATR Volatility Sizer catalog entry."""

    def test_strategy_import(self):
        """Test that the sizer can be imported from catalog."""
        from catalog.size.atr_volatility.strategy import (
            AtrVolatilitySizer as CatalogAtrVolatilitySizer,
        )
        assert CatalogAtrVolatilitySizer is AtrVolatilitySizer

    def test_registry_integration(self):
        """Test sizer is registered in SDK registry."""
        strategies = list_strategies(category="size")
        names = [s["name"] for s in strategies]
        assert "atr_volatility" in names

        sizer_class = get_strategy("atr_volatility")
        assert sizer_class is not None
        assert sizer_class.__name__ == "AtrVolatilitySizer"

    def test_config_defaults(self):
        """Test config default values."""
        sizer = AtrVolatilitySizer(
            target_risk_pct=Decimal("0.015"),
            atr_multiplier=Decimal("2.0"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )
        assert sizer.target_risk_pct == Decimal("0.015")
        assert sizer.atr_multiplier == Decimal("2.0")

    def test_inverse_vol_mode_basic(self):
        """Test basic inverse volatility sizing."""
        from honba.entities.instrument import InstrumentId

        from honba_strategies.components.sizers.base import Signal, SizingContext

        sizer = AtrVolatilitySizer(
            target_risk_pct=Decimal("0.015"),
            atr_multiplier=Decimal("2.0"),
            max_position_notional=Decimal("500000"),
            lot_size=Decimal("25"),
            freeze_limit=1800,
        )

        signal = Signal(
            direction=1,
            entry_price=Decimal("24000"),
            volatility_atr=Decimal("300"),
        )

        context = SizingContext(
            equity=Decimal("1000000"),
            cash_balance=Decimal("800000"),
            margin_used=Decimal("200000"),
            available_margin=Decimal("600000"),
            instrument_id=InstrumentId("NIFTY50", "NFO"),
            current_price=Decimal("24000"),
            atr=Decimal("300"),
        )

        result = sizer.calculate_size(signal, context)
        assert result.quantity == Decimal("25")
        assert result.stop_distance == Decimal("600")
        assert result.risk_at_stake == Decimal("15000")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])