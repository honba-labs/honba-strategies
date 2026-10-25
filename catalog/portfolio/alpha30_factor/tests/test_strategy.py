"""Tests for Alpha Factor strategy (catalog entry)."""


from honba_strategies.portfolio import AlphaFactorConfig, AlphaFactorStrategy


def test_alpha30_factor_catalog_entry():
    config = AlphaFactorConfig(
        name="alpha30_factor",
        symbol="",
        exchange="NSE",
        top_n=30,
    )
    strategy = AlphaFactorStrategy(config)
    assert strategy.name == "alpha30_factor"
    assert strategy.config.top_n == 30
