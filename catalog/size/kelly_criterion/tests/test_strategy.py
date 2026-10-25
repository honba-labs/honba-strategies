"""Tests for Kelly Criterion Sizer catalog entry."""

import pytest
from decimal import Decimal

from honba_strategies.components.sizers import KellySizer
from honba_strategies.core.registry import get_strategy, list_strategies


class TestKellyCriterionSizer:
    """Test Kelly Criterion Sizer catalog entry."""

    def test_strategy_import(self):
        """Test that the sizer can be imported from catalog."""
        from catalog.size.kelly_criterion.strategy import KellySizer as CatalogKellySizer
        assert CatalogKellySizer is KellySizer

    def test_registry_integration(self):
        """Test sizer is registered in SDK registry."""
        strategies = list_strategies(category="size")
        names = [s["name"] for s in strategies]
        assert "kelly_criterion" in names

        sizer_class = get_strategy("kelly_criterion")
        assert sizer_class is not None
        assert sizer_class.__name__ == "KellySizer"

    def test_config_defaults(self):
        """Test config default values."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
            kelly_fraction=Decimal("0.5"),
        )
        assert sizer.win_rate == Decimal("0.55")
        assert sizer.win_loss_ratio == Decimal("1.5")
        assert sizer.kelly_fraction == Decimal("0.5")

    def test_kelly_fraction_computation(self):
        """Test Kelly fraction computation."""
        sizer = KellySizer(
            win_rate=Decimal("0.55"),
            win_loss_ratio=Decimal("1.5"),
            kelly_fraction=Decimal("0.5"),
        )
        # Full Kelly = 0.55 - 0.45/1.5 = 0.25
        # Half Kelly = 0.125
        kelly = sizer._compute_kelly_fraction()
        assert kelly == Decimal("0.125")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])