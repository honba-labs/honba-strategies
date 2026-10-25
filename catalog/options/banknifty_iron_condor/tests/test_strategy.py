"""Tests for BankNifty Iron Condor catalog entry."""

import pytest
from decimal import Decimal

from honba_strategies.options import IronCondorConfig, IronCondorStrategy
from honba_strategies.core.registry import get_strategy, list_strategies


class TestBankNiftyIronCondor:
    """Test BankNifty Iron Condor Strategy."""

    def test_config_creation(self):
        """Test config creation with defaults."""
        config = IronCondorConfig(
            name="banknifty_iron_condor",
            symbol="BANKNIFTY",
            exchange="NFO",
        )

        assert config.name == "banknifty_iron_condor"
        assert config.symbol == "BANKNIFTY"
        assert config.exchange == "NFO"
        assert config.entry_time == "09:25"
        assert config.exit_time == "15:10"
        assert config.wing_width == 200
        assert config.short_delta == Decimal("0.16")
        assert config.profit_target_pct == Decimal("0.50")
        assert config.adjustment_delta == Decimal("0.30")
        assert config.lots == 1

    def test_config_validation(self):
        """Test config validation."""
        # Invalid wing_width
        with pytest.raises(ValueError, match="wing_width must be >= 50"):
            IronCondorConfig(
                name="test",
                symbol="BANKNIFTY",
                wing_width=25,
            )

        # Invalid lots
        with pytest.raises(ValueError, match="lots must be >= 1"):
            IronCondorConfig(
                name="test",
                symbol="BANKNIFTY",
                lots=0,
            )

        # Valid config
        config = IronCondorConfig(
            name="test",
            symbol="BANKNIFTY",
            wing_width=300,
            lots=2,
        )
        assert config.wing_width == 300
        assert config.lots == 2

    def test_strategy_creation(self):
        """Test strategy instantiation."""
        config = IronCondorConfig(
            name="banknifty_iron_condor",
            symbol="BANKNIFTY",
            exchange="NFO",
            capital=Decimal("1000000"),
            wing_width=200,
            lots=1,
        )

        strategy = IronCondorStrategy(config)
        assert strategy.name == "banknifty_iron_condor"
        assert strategy.config == config
        assert strategy.wing_width == 200
        assert strategy.short_delta == Decimal("0.16")
        assert not strategy.iron_condor_entered

    def test_strategy_parameters(self):
        """Test strategy parameter access."""
        config = IronCondorConfig(
            name="test",
            symbol="BANKNIFTY",
            wing_width=300,
            short_delta=Decimal("0.20"),
            profit_target_pct=Decimal("0.60"),
        )

        strategy = IronCondorStrategy(config)
        assert strategy.wing_width == 300
        assert strategy.short_delta == Decimal("0.20")
        assert strategy.profit_target_pct == Decimal("0.60")

    def test_registry_integration(self):
        """Test strategy is registered in SDK registry."""
        strategies = list_strategies(category="options")
        names = [s["name"] for s in strategies]
        assert "banknifty_iron_condor" in names

        strategy_class = get_strategy("banknifty_iron_condor")
        assert strategy_class is not None
        assert strategy_class.__name__ == "IronCondorStrategy"

    def test_config_serialization(self):
        """Test config TOML serialization."""
        config = IronCondorConfig(
            name="test",
            symbol="BANKNIFTY",
            wing_width=300,
        )

        data = config.to_dict()
        assert data["wing_width"] == "300"
        assert data["name"] == "test"

        config2 = IronCondorConfig.from_dict(data)
        assert config2.wing_width == 300

    def test_time_checking(self):
        """Test entry/exit time checking logic."""
        config = IronCondorConfig(
            name="test",
            symbol="BANKNIFTY",
            entry_time="09:25",
            exit_time="15:10",
        )
        strategy = IronCondorStrategy(config)

        class MockBar:
            def __init__(self, hour, minute):
                self.ts = type('ts', (), {'hour': hour, 'minute': minute})()
                self.close = Decimal("48000")

        # Before entry time
        bar = MockBar(9, 20)
        assert not strategy._is_entry_time(bar)

        # At entry time
        bar = MockBar(9, 25)
        assert strategy._is_entry_time(bar)

        # Before exit time
        bar = MockBar(15, 5)
        assert not strategy._is_exit_time(bar)

        # At exit time
        bar = MockBar(15, 10)
        assert strategy._is_exit_time(bar)

    def test_iron_condor_state_management(self):
        """Test iron condor entry/exit state."""
        config = IronCondorConfig(name="test", symbol="BANKNIFTY")
        strategy = IronCondorStrategy(config)

        assert not strategy.iron_condor_entered

        class MockBar:
            def __init__(self):
                self.close = Decimal("48000")
                self.ts = type('ts', (), {'hour': 9, 'minute': 25})()

        bar = MockBar()
        strategy._enter_iron_condor(bar)
        assert strategy.iron_condor_entered

        strategy._exit_iron_condor(bar)
        assert not strategy.iron_condor_entered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])