"""Tests for Calendar Spread catalog entry."""

import pytest
from decimal import Decimal

from honba_strategies.options import CalendarSpreadConfig, CalendarSpreadStrategy
from honba_strategies.core.registry import get_strategy, list_strategies


class TestCalendarSpread:
    """Test Calendar Spread Strategy."""

    def test_config_creation(self):
        """Test config creation with defaults."""
        config = CalendarSpreadConfig(
            name="calendar_spread",
            symbol="NIFTY",
            exchange="NFO",
        )

        assert config.name == "calendar_spread"
        assert config.symbol == "NIFTY"
        assert config.exchange == "NFO"
        assert config.strike_selection == "atm"
        assert config.near_expiry_days == 7
        assert config.far_expiry_days == 35
        assert config.profit_target_pct == Decimal("0.25")
        assert config.stop_loss_pct == Decimal("0.50")
        assert config.lots == 1

    def test_config_validation(self):
        """Test config validation."""
        # Invalid near_expiry >= far_expiry
        with pytest.raises(ValueError, match="near_expiry_days must be < far_expiry_days"):
            CalendarSpreadConfig(
                name="test",
                symbol="NIFTY",
                near_expiry_days=30,
                far_expiry_days=20,
            )

        # Invalid strike_selection
        with pytest.raises(ValueError, match="strike_selection must be atm, otm_call, or otm_put"):
            CalendarSpreadConfig(
                name="test",
                symbol="NIFTY",
                strike_selection="invalid",
            )

        # Invalid lots
        with pytest.raises(ValueError, match="lots must be >= 1"):
            CalendarSpreadConfig(
                name="test",
                symbol="NIFTY",
                lots=0,
            )

        # Valid config
        config = CalendarSpreadConfig(
            name="test",
            symbol="NIFTY",
            strike_selection="otm_call",
            near_expiry_days=5,
            far_expiry_days=30,
            lots=2,
        )
        assert config.strike_selection == "otm_call"
        assert config.near_expiry_days == 5
        assert config.far_expiry_days == 30
        assert config.lots == 2

    def test_strategy_creation(self):
        """Test strategy instantiation."""
        config = CalendarSpreadConfig(
            name="calendar_spread",
            symbol="NIFTY",
            exchange="NFO",
            capital=Decimal("1000000"),
            lots=1,
        )

        strategy = CalendarSpreadStrategy(config)
        assert strategy.name == "calendar_spread"
        assert strategy.config == config
        assert strategy.near_expiry_days == 7
        assert strategy.far_expiry_days == 35
        assert not strategy.spread_entered

    def test_registry_integration(self):
        """Test strategy is registered in SDK registry."""
        strategies = list_strategies(category="options")
        names = [s["name"] for s in strategies]
        assert "calendar_spread" in names

        strategy_class = get_strategy("calendar_spread")
        assert strategy_class is not None
        assert strategy_class.__name__ == "CalendarSpreadStrategy"

    def test_config_serialization(self):
        """Test config TOML serialization."""
        config = CalendarSpreadConfig(
            name="test",
            symbol="NIFTY",
            strike_selection="otm_put",
        )

        data = config.to_dict()
        assert data["strike_selection"] == "otm_put"
        assert data["name"] == "test"

        config2 = CalendarSpreadConfig.from_dict(data)
        assert config2.strike_selection == "otm_put"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])