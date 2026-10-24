"""Unit tests for TWAP execution strategy."""

from decimal import Decimal

from honba.domain import Bar, InstrumentId
from honba.strategies.testing import replay

from honba_strategies.execution import TwapConfig, TwapStrategy


def make_bars(closes, symbol="NIFTY50"):
    """Create bars from a list of closes."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, c, c, c, 1000.0) for i, c in enumerate(closes)]


class TestTwapStrategy:
    """Test TWAP execution strategy."""

    def build(self, **params):
        """Build TWAP strategy with config overrides."""
        config = TwapConfig(
            name="twap",
            symbol="NIFTY50",
            exchange="NSE",
            **params,
        )
        return TwapStrategy(config), config

    def test_twap_dispatches_slices_over_time(self):
        s, cfg = self.build(
            total_quantity=Decimal("300"),
            slice_size=Decimal("100"),
            duration_minutes=10,
            jitter_seconds=0,
            freeze_limit=1800,
        )
        # 12 bars = 12 minutes, should dispatch 3 slices
        closes = [100 + i * 0.1 for i in range(12)]
        result = replay(s, make_bars(closes, cfg.symbol))
        assert len(result.fills) == 3
        assert all(f.quantity == 100 for f in result.fills)

    def test_twap_respects_freeze_limit(self):
        s, _ = self.build(
            total_quantity=Decimal("500"),
            slice_size=Decimal("2000"),  # Exceeds freeze limit
            duration_minutes=10,
            freeze_limit=1800,
        )
        # Should cap at freeze_limit (slice_size is a Parameter descriptor, use _slice_size)
        assert s._slice_size == 1800

    def test_twap_no_trade_when_complete(self):
        s, cfg = self.build(
            total_quantity=Decimal("100"),
            slice_size=Decimal("100"),
            duration_minutes=60,
            jitter_seconds=0,
        )
        closes = [100] * 100  # Many bars
        result = replay(s, make_bars(closes, cfg.symbol))
        assert len(result.fills) == 1
        assert result.fills[0].quantity == 100