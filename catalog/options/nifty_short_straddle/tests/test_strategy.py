"""Tests for NIFTY Short Straddle catalog entry."""

from decimal import Decimal

import pytest

from honba_strategies.core.registry import get_strategy, list_strategies
from honba_strategies.options import ShortStraddleConfig, ShortStraddleStrategy


class TestNiftyShortStraddle:
    """Test NIFTY Short Straddle Strategy."""

    def test_config_creation(self):
        """Test config creation with defaults."""
        config = ShortStraddleConfig(
            name="nifty_short_straddle",
            symbol="NIFTY",
            exchange="NFO",
        )

        assert config.name == "nifty_short_straddle"
        assert config.symbol == "NIFTY"
        assert config.exchange == "NFO"
        assert config.entry_time == "09:20"
        assert config.exit_time == "15:15"
        assert config.sl_pct_per_leg == Decimal("0.25")
        assert config.combined_sl_pct == Decimal("0.20")
        assert config.profit_target_pct == Decimal("0.50")
        assert config.lots == 1
        assert config.max_positions == 1

    def test_config_validation(self):
        """Test config validation."""
        # Invalid lots
        with pytest.raises(ValueError, match="lots must be >= 1"):
            ShortStraddleConfig(
                name="test",
                symbol="NIFTY",
                lots=0,
            )

        # Valid config
        config = ShortStraddleConfig(
            name="test",
            symbol="NIFTY",
            lots=2,
        )
        assert config.lots == 2

    def test_strategy_creation(self):
        """Test strategy instantiation."""
        config = ShortStraddleConfig(
            name="nifty_short_straddle",
            symbol="NIFTY",
            exchange="NFO",
            capital=Decimal("1000000"),
            lots=1,
        )

        strategy = ShortStraddleStrategy(config)
        assert strategy.name == "nifty_short_straddle"
        assert strategy.config == config
        assert strategy.lots == 1
        assert not strategy.straddle_entered

    def test_strategy_parameters(self):
        """Test strategy parameter access."""
        config = ShortStraddleConfig(
            name="test",
            symbol="NIFTY",
            sl_pct_per_leg=Decimal("0.30"),
            combined_sl_pct=Decimal("0.25"),
        )

        strategy = ShortStraddleStrategy(config)
        assert strategy.sl_pct_per_leg == Decimal("0.30")
        assert strategy.combined_sl_pct == Decimal("0.25")
        assert strategy.profit_target_pct == Decimal("0.50")

    def test_registry_integration(self):
        """Test strategy is registered in SDK registry."""
        strategies = list_strategies(category="options")
        names = [s["name"] for s in strategies]
        assert "nifty_short_straddle" in names

        # Get strategy class via registry
        strategy_class = get_strategy("nifty_short_straddle")
        assert strategy_class is not None
        assert strategy_class.__name__ == "ShortStraddleStrategy"

    def test_config_serialization(self):
        """Test config TOML serialization."""
        config = ShortStraddleConfig(
            name="test",
            symbol="NIFTY",
            sl_pct_per_leg=Decimal("0.30"),
        )

        # to_dict
        data = config.to_dict()
        assert data["sl_pct_per_leg"] == "0.30"
        assert data["name"] == "test"

        # from_dict
        config2 = ShortStraddleConfig.from_dict(data)
        assert config2.sl_pct_per_leg == Decimal("0.30")

    def test_time_checking(self):
        """Test entry/exit time checking logic."""
        config = ShortStraddleConfig(
            name="test",
            symbol="NIFTY",
            entry_time="09:20",
            exit_time="15:15",
        )
        strategy = ShortStraddleStrategy(config)

        # Mock bar objects
        class MockBar:
            def __init__(self, hour, minute):
                self.ts = type('ts', (), {'hour': hour, 'minute': minute})()
                self.close = Decimal("24000")

        # Before entry time
        bar = MockBar(9, 15)
        assert not strategy._is_entry_time(bar)

        # At entry time
        bar = MockBar(9, 20)
        assert strategy._is_entry_time(bar)

        # After entry time
        bar = MockBar(10, 0)
        assert strategy._is_entry_time(bar)

        # Before exit time
        bar = MockBar(15, 10)
        assert not strategy._is_exit_time(bar)

        # At exit time
        bar = MockBar(15, 15)
        assert strategy._is_exit_time(bar)

    def test_straddle_state_management(self):
        """Test straddle entry/exit state."""
        config = ShortStraddleConfig(name="test", symbol="NIFTY")
        strategy = ShortStraddleStrategy(config)

        assert not strategy.straddle_entered
        assert strategy.call_entry_premium is None
        assert strategy.put_entry_premium is None

        # Simulate entry
        class MockBar:
            def __init__(self):
                self.close = Decimal("24000")
                self.ts = type('ts', (), {'hour': 9, 'minute': 20})()

        bar = MockBar()
        strategy._enter_straddle(bar)

        assert strategy.straddle_entered
        assert strategy.call_entry_premium is not None
        assert strategy.put_entry_premium is not None

        # Simulate exit
        strategy._exit_straddle(bar)
        assert not strategy.straddle_entered
        assert strategy.call_entry_premium is None
        assert strategy.put_entry_premium is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])