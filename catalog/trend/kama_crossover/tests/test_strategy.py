"""Tests for KAMA Crossover strategy (catalog entry)."""


from honba_strategies.trend import KamaConfig, KamaCrossoverStrategy


def test_kama_crossover_catalog_entry():
    """Verify the catalog entry can be imported and instantiated."""
    config = KamaConfig(
        name="kama_crossover",
        symbol="RELIANCE",
        exchange="NSE",
        fast_period=10,
        slow_period=30,
        er_period=10,
    )
    strategy = KamaCrossoverStrategy(config)
    assert strategy.name == "kama_crossover"
    assert strategy.config.fast_period == 10
    assert strategy.config.slow_period == 30
    assert strategy.config.er_period == 10