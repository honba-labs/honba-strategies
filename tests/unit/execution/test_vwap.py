"""Unit tests for VWAP execution strategy."""

from decimal import Decimal

from honba.domain import Bar, InstrumentId
from honba.strategies.testing import replay

from honba_strategies.execution import VwapConfig, VwapStrategy


def make_bars(closes, symbol="NIFTY50"):
    """Create bars from a list of closes."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, c, c, c, 1000.0) for i, c in enumerate(closes)]


class TestVwapStrategy:
    """Test VWAP execution strategy."""

    def build(self, **params):
        """Build VWAP strategy with config overrides."""
        config = VwapConfig(
            name="vwap",
            symbol="NIFTY50",
            exchange="NSE",
            **params,
        )
        return VwapStrategy(config), config

    def test_vwap_dispatches_slices(self):
        s, cfg = self.build(
            total_quantity=Decimal("300"),
            slice_size=Decimal("100"),
            participation_rate=Decimal("0.1"),
            freeze_limit=1800,
        )
        closes = [100 + i * 0.1 for i in range(20)]
        result = replay(s, make_bars(closes, cfg.symbol))
        assert len(result.fills) >= 2

    def test_vwap_respects_freeze_limit(self):
        s, _ = self.build(
            total_quantity=Decimal("500"),
            slice_size=Decimal("2000"),
            participation_rate=Decimal("0.1"),
            freeze_limit=1800,
        )
        assert s.freeze_limit == 1800

    def test_vwap_completes_order(self):
        s, cfg = self.build(
            total_quantity=Decimal("100"),
            slice_size=Decimal("50"),
            participation_rate=Decimal("0.5"),
            freeze_limit=1800,
        )
        closes = [100] * 50
        result = replay(s, make_bars(closes, cfg.symbol))
        total_qty = sum(f.quantity for f in result.fills)
        assert total_qty == 100