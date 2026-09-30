from pathlib import Path

import pytest

from honba.entities.bar import Bar
from honba.entities.instrument import InstrumentId
from honba.entities.order import OrderSide
from honba.strategies.config import StrategyConfig
from honba.strategies.indicators import build_indicator
from honba.strategies.testing import replay

HERE = Path(__file__).resolve().parent.parent
MIN = 60_000_000_000
DAY = 86_400_000_000_000
IST = 330 * MIN


def build(load_strategy, indicator=None, **params):
    mod = load_strategy(HERE)
    cfg = StrategyConfig.from_toml(HERE / "config.toml")
    cfg.params.update(params)
    cfg.indicators["vwap"].update(indicator or {})
    return mod.VwapReversion(cfg), cfg


def session(closes, start="09:15", day=20_000, step=5, symbol="NIFTY50"):
    """5-minute bars from `start` IST on IST-day `day`; high=low=close, volume 1000."""
    iid = InstrumentId(symbol, "NSE")
    h, m = map(int, start.split(":"))
    t0 = day * DAY + (h * 60 + m) * MIN - IST
    return [Bar(iid, t0 + i * step * MIN, c, c, c, c, 1000.0) for i, c in enumerate(closes)]


CALM = [100, 101, 99, 100, 101, 99]  # session VWAP ~ 100, small dispersion
DIP_THEN_RECOVER = CALM + [95, 96, 98, 100.5, 101]


def test_config_declares_vwap(load_strategy):
    assert StrategyConfig.from_toml(HERE / "config.toml").indicators["vwap"]["kind"] == "vwap"


def test_buys_below_lower_band_and_exits_at_vwap(load_strategy):
    s, cfg = build(load_strategy, capital=100_000.0, allocation=1.0)
    bars = session(DIP_THEN_RECOVER, symbol=cfg.symbol)
    result = replay(s, bars)
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    ref = build_indicator("vwap", **{k: v for k, v in cfg.indicators["vwap"].items() if k != "kind"})
    levels = [ref.update_bar(b) for b in bars]
    assert bars[6].close < levels[6].lower  # the dip bar really is below the band
    assert result.fills[0].ts == bars[6].ts
    sell_bar = next(b for b, v in zip(bars[7:], levels[7:]) if b.close >= v.vwap)
    assert result.fills[1].ts == sell_bar.ts


def test_no_new_entries_after_cutoff(load_strategy):
    s, cfg = build(load_strategy, entry_cutoff="14:30")
    late = session(DIP_THEN_RECOVER, start="14:35", symbol=cfg.symbol)  # dip happens after 14:30
    assert replay(s, late).fills == []


def test_squares_off_before_the_close(load_strategy):
    s, cfg = build(load_strategy, squareoff="15:15", entry_cutoff="15:00")
    # dip at ~14:55 then no recovery; the 15:15 bar must flatten the position
    closes = CALM + [95, 94, 93, 92, 91, 90]  # 12 bars: 14:20 ... 15:15
    bars = session(closes, start="14:20", symbol=cfg.symbol)  # bars at 14:20 ... 14:40, 14:45(dip) ...
    result = replay(s, bars)
    assert [f.side for f in result.fills][-1] is OrderSide.SELL
    assert s.position(cfg.instrument_id) == 0
    assert result.fills[-1].ts >= bars[0].ts + 55 * MIN  # sold at/after 15:15, not before


def test_no_overnight_carry_each_session_starts_flat(load_strategy):
    s, cfg = build(load_strategy)
    day1 = session(DIP_THEN_RECOVER[:8], day=20_000, symbol=cfg.symbol)  # ends holding after the dip
    day2 = session(CALM, day=20_001, symbol=cfg.symbol)
    result = replay(s, day1 + day2)
    # a position still open when the next IST session starts is flattened on that first bar
    assert s.position(cfg.instrument_id) == 0
    assert result.fills[-1].side is OrderSide.SELL and result.fills[-1].ts == day2[0].ts


def test_invalid_config(load_strategy):
    for bad in (dict(entry_cutoff="25:00"), dict(squareoff="nope"), dict(capital=0), dict(allocation=0)):
        with pytest.raises(ValueError):
            build(load_strategy, **bad)
    with pytest.raises(ValueError):
        build(load_strategy, entry_cutoff="15:20", squareoff="15:15")  # cutoff must precede square-off
