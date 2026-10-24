"""Unit tests for POV execution strategy."""

from decimal import Decimal

from honba.domain import Bar, InstrumentId
from honba.strategies.testing import replay

from honba_strategies.execution import PovConfig, PovStrategy


def make_bars(closes, symbol="NIFTY50"):
    """Create bars from a list of closes."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, c, c, c, 1000.0) for i, c in enumerate(closes)]


class TestPovStrategy:
    """Test POV execution strategy."""

    def build(self, **params):
        """Build POV strategy with config overrides."""
        config = PovConfig(
            name="pov",
            symbol="NIFTY50",
            exchange="NSE",
            **params,
        )
        return PovStrategy(config), config

    def test_pov_dispatches_slices(self):
        s, cfg = self.build(
            total_quantity=Decimal("300"),
            target_rate=Decimal("0.1"),
            max_slice_size=Decimal("100"),
            min_slice_size=Decimal("10"),
            freeze_limit=1800,
            volume_window=5,
        )
        closes = [100 + i * 0.1 for i in range(20)]
        result = replay(s, make_bars(closes, cfg.symbol))
        assert len(result.fills) >= 2

    def test_pov_respects_freeze_limit(self):
        s, _ = self.build(
            total_quantity=Decimal("500"),
            target_rate=Decimal("0.5"),
            max_slice_size=Decimal("5000"),
            min_slice_size=Decimal("10"),
            freeze_limit=1800,
            volume_window=5,
        )
        assert s.max_slice_size == 1800

    def test_pov_completes_order(self):
        s, cfg = self.build(
            total_quantity=Decimal("100"),
            target_rate=Decimal("0.5"),
            max_slice_size=Decimal("50"),
            min_slice_size=Decimal("10"),
            freeze_limit=1800,
            volume_window=3,
        )
        closes = [100] * 20
        result = replay(s, make_bars(closes, cfg.symbol))
        total_qty = sum(f.quantity for f in result.fills)
        assert total_qty == 100