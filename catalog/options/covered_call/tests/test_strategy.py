"""Tests for Covered Call catalog entry."""

import pytest
from decimal import Decimal

from honba_strategies.options import CoveredCallConfig, CoveredCallStrategy
from honba_strategies.core.registry import get_strategy, list_strategies


class TestCoveredCall:
    """Test Covered Call Strategy."""

    def test_config_creation(self):
        """Test config creation with defaults."""
        config = CoveredCallConfig(
            name="covered_call",
            symbol="RELIANCE",
            exchange="NSE",
        )

        assert config.name == "covered_call"
        assert config.symbol == "RELIANCE"
        assert config.exchange == "NSE"
        assert config.otm_pct == Decimal("0.05")
        assert config.roll_days_before_expiry == 2
        assert config.min_premium_yield == Decimal("0.01")
        assert config.max_assignment_risk == Decimal("0.30")
        assert config.quantity == 100

    def test_config_validation(self):
        """Test config validation."""
        # Invalid quantity
        with pytest.raises(ValueError, match="quantity must be >= 1"):
            CoveredCallConfig(
                name="test",
                symbol="RELIANCE",
                quantity=0,
            )

        # Invalid otm_pct
        with pytest.raises(ValueError, match="otm_pct must be >= 0"):
            CoveredCallConfig(
                name="test",
                symbol="RELIANCE",
                otm_pct=Decimal("-0.01"),
            )

        # Valid config
        config = CoveredCallConfig(
            name="test",
            symbol="RELIANCE",
            quantity=200,
            otm_pct=Decimal("0.08"),
        )
        assert config.quantity == 200
        assert config.otm_pct == Decimal("0.08")

    def test_strategy_creation(self):
        """Test strategy instantiation."""
        config = CoveredCallConfig(
            name="covered_call",
            symbol="RELIANCE",
            exchange="NSE",
            capital=Decimal("1000000"),
            quantity=100,
        )

        strategy = CoveredCallStrategy(config)
        assert strategy.name == "covered_call"
        assert strategy.config == config
        assert strategy.quantity == 100
        assert not strategy.covered_call_active

    def test_registry_integration(self):
        """Test strategy is registered in SDK registry."""
        strategies = list_strategies(category="options")
        names = [s["name"] for s in strategies]
        assert "covered_call" in names

        strategy_class = get_strategy("covered_call")
        assert strategy_class is not None
        assert strategy_class.__name__ == "CoveredCallStrategy"

    def test_config_serialization(self):
        """Test config TOML serialization."""
        config = CoveredCallConfig(
            name="test",
            symbol="RELIANCE",
            otm_pct=Decimal("0.08"),
        )

        data = config.to_dict()
        assert data["otm_pct"] == "0.08"
        assert data["name"] == "test"

        config2 = CoveredCallConfig.from_dict(data)
        assert config2.otm_pct == Decimal("0.08")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])