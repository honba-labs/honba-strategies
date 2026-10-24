"""Unit tests for Iceberg execution strategy."""

from decimal import Decimal

from honba.domain import Bar, InstrumentId
from honba.strategies.testing import replay

from honba_strategies.execution import IcebergConfig, IcebergStrategy


def make_bars(closes, symbol="NIFTY50"):
    """Create bars from a list of closes."""
    iid = InstrumentId(symbol, "NSE")
    return [Bar(iid, i + 1, c, c, c, c, 1000.0) for i, c in enumerate(closes)]


class TestIcebergStrategy:
    """Test Iceberg execution strategy."""

    def build(self, **params):
        """Build Iceberg strategy with config overrides."""
        config = IcebergConfig(
            name="iceberg",
            symbol="NIFTY50",
            exchange="NSE",
            **params,
        )
        return IcebergStrategy(config), config

    def test_iceberg_replenishes_on_fill(self):
        s, cfg = self.build(
            total_quantity=Decimal("300"),
            display_size=Decimal("100"),
            display_variance=Decimal("0.0"),
            freeze_limit=1800,
            min_refill_interval=0,
            price_limit=Decimal("0.0"),
        )
        closes = [100] * 10
        result = replay(s, make_bars(closes, cfg.symbol))
        assert len(result.fills) >= 2
        total_qty = sum(f.quantity for f in result.fills)
        assert total_qty == 300

    def test_iceberg_respects_freeze_limit(self):
        s, _ = self.build(
            total_quantity=Decimal("500"),
            display_size=Decimal("2000"),
            display_variance=Decimal("0.0"),
            freeze_limit=1800,
            min_refill_interval=0,
            price_limit=Decimal("0.0"),
        )
        assert s.display_size == 1800

    def test_iceberg_completes_order(self):
        s, cfg = self.build(
            total_quantity=Decimal("200"),
            display_size=Decimal("50"),
            display_variance=Decimal("0.0"),
            freeze_limit=1800,
            min_refill_interval=0,
            price_limit=Decimal("0.0"),
        )
        closes = [100] * 20
        result = replay(s, make_bars(closes, cfg.symbol))
        total_qty = sum(f.quantity for f in result.fills)
        assert total_qty == 200