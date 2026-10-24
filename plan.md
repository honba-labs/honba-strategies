# Master Plan: 本場・策 honba-strategies (Python Strategy SDK & Catalog Architecture)

> **The production quantitative strategy SDK and algorithmic catalog for the Honba platform.**  
> Houses battle-tested algorithmic trading strategies, institutional execution algorithms, statistical arbitrage models, high-frequency quoting engines, and dynamic portfolio rebalancers ported from **StockSharp (`StockSharp.Algo.Strategies`)** and modernized for Indian financial markets (NSE, BSE, NFO, MCX) and global multi-asset trading.  
> Packaged as a standard, typed, pip-installable Python SDK (`honba-strategies`), powered by the compiled Rust kernel (`honba-core` / `honba-tamashii`), 100% exact 128-bit decimal arithmetic, and strict research-live parity.

---

## 0. Executive Summary & Problem Diagnosis: "From File Dump to Production SDK"

### 0.1 The Problem: Current Source Code Dump
Historically, `honba-strategies` originated as a flat, unorganized file dump. Strategies were scaffolded as loose folders scattered directly across the repository root (`momentum/`, `options/`, `mean_reversion/`, `etf/`, `intraday/`, `mutual_funds/`, `swing/`, `portfolio/`, `universe/`, `ai_generated/`). 

This resulted in severe architectural entropy:
1. **Root Directory Sprawl**: Over 10 strategy domain directories were dumped at the repository root, polluting the project namespace alongside standard packaging files.
2. **Hollow Scaffolds & Dead Code**: Dozens of strategy subdirectories contain only 30-byte stub files (`"""Strategy: xyz"""`), unpopulated 22-byte `backtest_result.json` files, or obsolete copy-paste boilerplate.
3. **Scattered & Broken Test Harness**: Test scripts were dumped directly into the repository root (`test_catalog_fills.py`, `test_readme_sections.py`, `test_registry.py`, `test_step_chain.py`, `test_step_manifests.py`). A conflicting `pytest.ini` at the root caused test discovery failures due to missing module pathing for `tools`.
4. **Split-Brain Catalog Registry (`registry.json`)**: Half of the registry entries point to modernized `catalog/` paths (`catalog/execution/...`, `catalog/arbitrage/...`), while the remaining entries still point to obsolete root dump paths (`momentum/trend/...`, `universe/alpha/...`).
5. **Ambiguous Separation of Concerns**: Unclear boundaries between what is an installable, importable library (`honba_strategies`), what is a declarative step manifest for visual chaining (`catalog/`), what is developer tooling (`tools/`), and what is testing infrastructure (`tests/`).

### 0.2 The Solution: The 4-Zone Clean Architecture
Now that `honba-strategies` is packaged as a standard Python `src/` package (`pyproject.toml` + `src/honba_strategies/`), the repository must undergo a **complete source code restructuring**. 

Every file in the repository must reside in one of four strictly segregated zones:
- **Zone 1: Production Python SDK (`src/honba_strategies/`)**: The typed, pip-installable library containing all strategy algorithms, mathematical models, execution logic, and reusable components.
- **Zone 2: Declarative Strategy Catalog (`catalog/`)**: Declarative metadata (`step.toml`, `config.toml`, `README.md`) and thin catalog wrappers (`strategy.py`) for visual workflow chaining and discovery.
- **Zone 3: Centralized Test Suite (`tests/`)**: Fully organized test tree (`tests/unit/`, `tests/integration/`, `tests/parity/`, `tests/catalog/`), eliminating all test scripts from the root directory.
- **Zone 4: Developer Tools, Schemas & Documentation (`tools/`, `schema/`, `docs/`)**: Step schema validation engines, chain linters, and developer utilities.

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      honba-strategies Python SDK                       │
 ├────────────────────────────┬───────────────────────────────────────────┤
 │ Execution (StockSharp)     │ TWAP, VWAP, Percentage of Volume, Iceberg │
 │ Arbitrage (StockSharp)     │ Statistical Pairs, Cash-and-Carry, Basket │
 │ Market Making (StockSharp) │ Avellaneda-Stoikov, Spread Quoting, Ladder│
 │ Trend & Breakout           │ Turtle (Donchian), KAMA, Multi-Supertrend │
 │ Mean Reversion             │ Bollinger-RSI, VWAP Bands, Ornstein-Uhlen.│
 │ Portfolio Management       │ Risk Parity, Mean-Variance MVO, Equal Wt  │
 │ Options & Volatility       │ Short Straddle, Iron Condor, Calendar     │
 ├────────────────────────────┴───────────────────────────────────────────┤
 │ Composable Components: Reusable Signals + Sizers + Indian Risk Guards  │
 ├────────────────────────────────────────────────────────────────────────┤
 │ Runtime & Kernel: honba (honba-tamashii) + Decimal Math (honba-core)   │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Architectural Invariants & Deduplication (Separation of Concerns)

To avoid code duplication and architectural drift across the Honba workspace, the division of responsibilities is strictly enforced:

### 1.1 Strict Deduplication with `honba` Core (`honba-tamashii`)
- **`honba` (`honba-tamashii`)**: Owns the core runtime engine, execution ports (`ExecutionPort`), ledger context (`StrategyContext`, `LedgerContext`), runner harnesses (`runner.py`, `replay`), basic parameter descriptors (`Parameter`), base strategy lifecycle ABCs (`Strategy`, `SlicingStrategy`, `QuotingStrategy`, `ArbitrageStrategy`, `RebalancingStrategy`, `PortfolioStrategy`), and vectorized indicator math (`honba.strategies.indicators`).
- **`honba-strategies` (This SDK)**:
  - **Does NOT** define low-level strategy ABCs or re-implement indicator calculation kernels.
  - **Directly subclasses** `honba.strategies.base.*` primitives to build concrete, production-ready, hyperparameterized trading strategies.
  - Implements institutional execution logic, statistical modeling (cointegration tests, Ornstein-Uhlenbeck stochastic fitting), and risk-managed execution loops.
  - Provides pluggable building blocks: Alpha Signal generators, Position Sizing models, and Indian Regulatory Guardrails.

### 1.2 Python SDK Standards
- **PEP 517 / PEP 621 Packaging**: Standard `pyproject.toml` using `setuptools` (with `packages.find` under `src/`).
- **`src`-Layout**: Source code strictly isolated under `src/honba_strategies/` to guarantee import parity between development checkouts and installed wheels.
- **Strict Typing (PEP 561)**: Includes `py.typed` marker; passes `pyright` and `mypy` in strict mode with 100% typed public APIs.
- **Structured Configuration**: Parameter schemas defined via declarative `Parameter` descriptors and validated via typed config dataclasses/Pydantic models.
- **Exact Decimal Arithmetic**: 100% exact price, quantity, and cash accounting using `Decimal` / `rust_decimal`. Floats are confined strictly to statistical metrics (z-scores, half-life, correlations, Greeks).

### 1.3 First-Class Indian Market Microstructure
- **SEBI & Exchange Conformance**: Dynamic single-order freeze limit slicing (e.g. NIFTY 1,800 contracts), Order-to-Trade Ratio (OTR) safety margins, mandatory SEBI Algo ID tagging, and scrip operational circuit bands.
- **Intraday & Settlement Realities**: Automatic MIS 15:20 IST square-off enforcement, T+1 Demat settlement calendar awareness, and statutory cost accounting (STT, GST, Stamp Duty, Exchange Turnover fees).

---

## 2. Source Code Restructuring: Before vs After

### 2.1 The Current State: "The Root Dump"
```text
honba-strategies/ (CURRENT DUMP)
├── pyproject.toml
├── registry.json                       # Mixed paths: catalog/... vs legacy root dirs
├── pytest.ini                          # Conflicts with pyproject.toml; breaks test runner
├── conftest.py                         # Root-level test harness config
├── test_catalog_fills.py               # Dumped at root
├── test_readme_sections.py             # Dumped at root
├── test_registry.py                    # Dumped at root
├── test_step_chain.py                  # Dumped at root
├── test_step_manifests.py              # Dumped at root
├── etf/                                # DUMP: 4 hollow scaffold stubs
├── intraday/                           # DUMP: 4 hollow scaffold stubs
├── mean_reversion/                     # DUMP: 5 hollow scaffold stubs across 3 subdirs
├── momentum/                           # DUMP: 7 hollow scaffold stubs across 3 subdirs
├── mutual_funds/                       # DUMP: 4 hollow scaffold stubs
├── options/                            # DUMP: 5 hollow scaffold stubs
├── portfolio/                          # DUMP: 1 legacy strategy + nested test folder
├── swing/                              # DUMP: 3 hollow scaffold stubs
├── universe/                           # DUMP: 5 alpha factor stubs
├── ai_generated/                       # DUMP: Obsolete empty scaffold
├── catalog/                            # INCOMPLETE: Only execution/ and arbitrage/
├── src/                                # INCOMPLETE: Missing domains & components
└── tests/                              # INCOMPLETE: Root test files not integrated
```

### 2.2 The Clean Target State: "The 4-Zone Production Architecture"
```text
honba-strategies/ (CLEAN RESTRUCTURED TARGET)
├── pyproject.toml                     # Single source of truth for build, ruff, mypy, pytest
├── README.md                          # SDK user guide, quickstart & catalog docs
├── LICENSE                            # AGPL-3.0 License
├── registry.json                      # Canonical strategy discovery index (all paths -> catalog/...)
│
├── src/                               # ZONE 1: Production Python SDK (honba_strategies)
│   └── honba_strategies/
│       ├── __init__.py                # Top-level public SDK exports & __version__
│       ├── py.typed                   # PEP 561 typing marker
│       ├── cli.py                     # Typer CLI application (`honba-strategies`)
│       ├── core/                      # SDK foundational abstractions & registry engine
│       │   ├── __init__.py
│       │   ├── config.py              # Base StrategyConfig, parameter binding & serialization
│       │   ├── errors.py              # Typed error hierarchy (HonbaStrategyError, RiskLimitExceeded)
│       │   └── registry.py            # SDK StrategyRegistry & @register_strategy decorator
│       ├── execution/                 # Institutional Slicing & Execution (StockSharp Port)
│       │   ├── __init__.py            # TwapStrategy, VwapStrategy, PovStrategy, IcebergStrategy
│       │   ├── twap.py                # Time-Weighted Average Price with microsecond jitter
│       │   ├── vwap.py                # Volume-Weighted Average Price with intraday profile
│       │   ├── pov.py                 # Percentage of Volume dynamic participation
│       │   └── iceberg.py             # Synthetic iceberg display & replenish
│       ├── arbitrage/                 # Relative Value & Arbitrage (StockSharp Port)
│       │   ├── __init__.py            # PairsTradingStrategy, CashAndCarryStrategy, BasketArbitrage
│       │   ├── pairs.py               # Cointegration & z-score dual-leg statistical arbitrage
│       │   ├── cash_and_carry.py      # Spot vs near-month future statutory basis arbitrage
│       │   └── basket.py              # Index ETF vs synthetic basket creation/redemption
│       ├── market_making/             # High-Frequency Liquidity Provision (StockSharp Port)
│       │   ├── __init__.py            # AvellanedaStoikovStrategy, SpreadQuoting, LadderQuoting
│       │   ├── avellaneda_stoikov.py  # Inventory-risk reservation price quoting engine
│       │   ├── spread.py              # Best bid/ask pegging with order book imbalance skew
│       │   └── ladder.py              # Multi-tier grid quoting with inventory decay
│       ├── trend/                     # Trend Following & Breakout (StockSharp Port)
│       │   ├── __init__.py            # TurtleStrategy, KamaCrossover, Supertrend, Breakout
│       │   ├── turtle.py              # Richard Dennis Donchian breakout & N-ATR pyramiding
│       │   ├── kama.py                # Kaufman Adaptive Moving Average noise-filtered cross
│       │   ├── supertrend.py          # Multi-timeframe ATR trailing breakout
│       │   └── breakout.py            # Volatility channel and range breakout engine
│       ├── mean_reversion/            # Statistical & Volatility Mean Reversion (StockSharp Port)
│       │   ├── __init__.py            # BollingerRsiStrategy, VwapBands, OrnsteinUhlenbeck
│       │   ├── bollinger_rsi.py       # Bollinger envelope deviation + RSI exhaustion
│       │   ├── vwap_bands.py          # Session VWAP 2.5σ intraday mean reversion
│       │   └── ornstein_uhlenbeck.py  # Continuous-time OU stochastic process mean reversion
│       ├── portfolio/                 # Dynamic Allocation & Rebalancing (StockSharp Port)
│       │   ├── __init__.py            # EqualWeightRebalancer, RiskParity, Markowitz, AlphaFactor
│       │   ├── equal_weight.py        # Drift-band periodic rebalancing strategy
│       │   ├── risk_parity.py         # Equal risk contribution inverse-volatility allocation
│       │   ├── markowitz.py           # Mean-variance quadratic optimization with sector bounds
│       │   └── alpha_factors.py       # Multi-factor portfolio selection & factor weighting
│       ├── options/                   # Options & Volatility Trading
│       │   ├── __init__.py            # ShortStraddleStrategy, IronCondor, CoveredCall, Calendar
│       │   ├── straddle.py            # ATM Short Straddle with delta-hedge and stop-loss
│       │   ├── iron_condor.py         # 4-leg defined risk range-bound volatility capture
│       │   ├── covered_call.py        # Long underlying delivery + Short OTM call writing
│       │   └── calendar.py            # Time-decay term structure calendar spread
│       ├── etf_funds/                 # ETF & Systematic Fund Strategies
│       │   ├── __init__.py            # GoldEquityRotation, SectorRotation, TrackingErrorArb
│       │   ├── rotation.py            # Dual-momentum and relative strength asset class rotation
│       │   └── tracking_arb.py        # NAV vs market price tracking error arbitrage
│       ├── intraday/                  # Microstructure & Intraday Equity Patterns
│       │   ├── __init__.py            # GapFillStrategy, OrbStrategy, PivotBounceStrategy
│       │   ├── gap_fill.py            # Morning opening gap mean reversion
│       │   ├── orb.py                 # Opening Range Breakout with time-decay stops
│       │   └── pivot_bounce.py        # Classical floor pivot support/resistance bounce
│       └── components/                # Reusable Strategy Building Blocks
│           ├── __init__.py
│           ├── signals/               # Alpha & technical signals (OU-fit, cointegration, z-scores)
│           ├── sizers/                # Position sizers (ATR volatility sizing, Kelly, target risk)
│           └── risk/                  # Indian risk guards (OTR monitor, drawdown halt, MIS 15:20)
│
├── catalog/                           # ZONE 2: Declarative Strategy Catalog (Visual Chaining)
│   ├── execution/                     # Slicing steps (twap, vwap, pov, iceberg)
│   ├── arbitrage/                     # Arbitrage steps (pairs, cash_and_carry, basket)
│   ├── market_making/                 # Quoting steps (spread, avellaneda_stoikov, ladder)
│   ├── trend/                         # Trend steps (turtle, kama, supertrend, sma_cross)
│   ├── mean_reversion/                # Reversion steps (bollinger_rsi, vwap_bands, ou)
│   ├── portfolio/                     # Rebalancing steps (equal_weight, risk_parity, markowitz)
│   ├── options/                       # Options steps (short_straddle, iron_condor, covered_call)
│   ├── etf_funds/                     # ETF rotation steps (gold_equity, sector_rotation)
│   └── intraday/                      # Intraday steps (gap_fill, orb, pivot_bounce)
│       └── <strategy_name>/
│           ├── step.toml              # Declarative step manifest (contracts, bounds, types)
│           ├── config.toml            # Default execution configuration
│           ├── README.md              # Mathematical formulas, parameter table, benchmarks
│           ├── strategy.py            # Thin catalog entry importing from honba_strategies
│           └── tests/
│               └── test_strategy.py   # Catalog parameter instantiation and contract verification
│
├── tests/                             # ZONE 3: Centralized Test Suite (Zero Root Pollution)
│   ├── conftest.py                    # Centralized pytest fixtures & test harness environment
│   ├── unit/                          # Isolated unit tests for Python SDK modules
│   │   ├── execution/                 # Unit tests for TWAP, VWAP, POV, Iceberg
│   │   ├── arbitrage/                 # Unit tests for Pairs, Cash-and-Carry, Basket
│   │   ├── market_making/             # Unit tests for Quoting & Inventory reservation
│   │   ├── trend/                     # Unit tests for Turtle, KAMA, Supertrend
│   │   ├── mean_reversion/            # Unit tests for Bollinger-RSI, VWAP Bands, OU
│   │   ├── portfolio/                 # Unit tests for Equal Weight, Risk Parity, MVO
│   │   ├── options/                   # Unit tests for Straddles, Condors, Calendars
│   │   └── components/                # Unit tests for Signals, Sizers, Risk Guards
│   ├── integration/                   # Lifecycle & delayed fill simulated execution tests
│   ├── parity/                        # Golden vector numerical parity vs StockSharp C#
│   └── catalog/                       # Centralized Catalog & Manifest Verification Tests
│       ├── test_registry.py           # Validates registry.json consistency against catalog/
│       ├── test_step_manifests.py     # Validates all step.toml files against step.schema.json
│       ├── test_step_chain.py         # Validates pipeline chaining compatibility rules
│       ├── test_catalog_fills.py      # Simulates execution fills across all catalog entries
│       └── test_readme_sections.py    # Ensures every strategy README has required sections
│
├── tools/                             # ZONE 4: Developer Tools & Automation
│   ├── __init__.py
│   ├── mini_schema.py                 # Lightweight pure-Python JSON schema validator
│   ├── validate_chain.py              # CLI and library validator for step chaining
│   └── catalog_sync.py                # Automated synchronizer between SDK code and step.toml
│
├── schema/                            # Schema Specifications
│   ├── step.schema.json               # JSON Schema for declarative step manifests
│   └── README.md                      # Schema documentation & type contract rules
│
└── docs/                              # Architecture & Reference Documentation
```

### 2.3 Strict Root Cleanliness Rules
The repository root must be kept 100% clean of exploratory dumps, ad-hoc test scripts, and scaffold stubs.
- **Strictly Allowed at Root**: `pyproject.toml`, `README.md`, `LICENSE`, `registry.json`, `.gitignore`, `.github/`, `.agents/`, and the four canonical directory roots (`src/`, `catalog/`, `tests/`, `tools/`, `schema/`, `docs/`).
- **Strictly Prohibited at Root**:
  - NO strategy folders (`etf/`, `intraday/`, `mean_reversion/`, `momentum/`, `mutual_funds/`, `options/`, `portfolio/`, `swing/`, `ai_generated/`, `universe/`).
  - NO test scripts (`test_*.py`). All tests live strictly in `tests/`.
  - NO ad-hoc config files (`pytest.ini` — all tool configs must reside in `pyproject.toml`).
  - NO orphaned `backtest_result.json` or `.pyc` caches.

---

## 3. Comprehensive Dump Inventory & Migration Matrix

Every single legacy file currently dumped in the repository has been audited and mapped to its target destination:

| Current Dump Path | Current Content / Status | Target SDK Location (`src/`) | Target Catalog Path (`catalog/`) | Target Test Path (`tests/`) | Action Required |
|:---|:---|:---|:---|:---|:---|
| **Root Tests** | | | | | |
| `test_registry.py` | Validates `registry.json` consistency | N/A | N/A | `tests/catalog/test_registry.py` | Move to `tests/catalog/`; fix `ROOT` path resolution |
| `test_step_manifests.py` | Validates `step.toml` against JSON schema | N/A | N/A | `tests/catalog/test_step_manifests.py` | Move to `tests/catalog/`; fix `tools` import path |
| `test_step_chain.py` | Validates step chaining compatibility | N/A | N/A | `tests/catalog/test_step_chain.py` | Move to `tests/catalog/`; fix `tools` import path |
| `test_catalog_fills.py` | Verifies fill simulation across strategies | N/A | N/A | `tests/catalog/test_catalog_fills.py` | Move to `tests/catalog/`; fix `ROOT` path resolution |
| `test_readme_sections.py` | Validates README documentation sections | N/A | N/A | `tests/catalog/test_readme_sections.py` | Move to `tests/catalog/`; fix `ROOT` path resolution |
| `pytest.ini` | Root pytest override causing import errors | N/A | N/A | Consolidated in `pyproject.toml` | Delete `pytest.ini`; manage in `pyproject.toml` |
| `conftest.py` | Root test configuration | N/A | N/A | `tests/conftest.py` | Move into `tests/` with proper `sys.path` injection |
| **`options/`** | | | | | |
| `options/nifty_short_straddle` | 37-byte scaffold stub | `honba_strategies.options.straddle` | `catalog/options/nifty_short_straddle` | `tests/unit/options/test_straddle.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `options/banknifty_iron_condor` | 37-byte scaffold stub | `honba_strategies.options.iron_condor` | `catalog/options/banknifty_iron_condor` | `tests/unit/options/test_iron_condor.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `options/covered_call` | 37-byte scaffold stub | `honba_strategies.options.covered_call` | `catalog/options/covered_call` | `tests/unit/options/test_covered_call.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `options/expiry_day_scalp` | 37-byte scaffold stub | `honba_strategies.options.expiry_scalp` | `catalog/options/expiry_day_scalp` | `tests/unit/options/test_expiry_scalp.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `options/calendar_spread` | 37-byte scaffold stub | `honba_strategies.options.calendar` | `catalog/options/calendar_spread` | `tests/unit/options/test_calendar.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| **`momentum/`** | | | | | |
| `momentum/trend/sma_crossover` | Scaffold stub with `step.toml` | `honba_strategies.trend.sma` | `catalog/trend/sma_crossover` | `tests/unit/trend/test_sma.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `momentum/trend/macd_trend` | Scaffold stub with `step.toml` | `honba_strategies.trend.macd` | `catalog/trend/macd_trend` | `tests/unit/trend/test_macd.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `momentum/trend/donchian_trend` | Scaffold stub with `step.toml` | `honba_strategies.trend.donchian` | `catalog/trend/donchian_trend` | `tests/unit/trend/test_donchian.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `momentum/trend/turtle_20` | Scaffold stub with `step.toml` | `honba_strategies.trend.turtle` | `catalog/trend/turtle_20` | `tests/unit/trend/test_turtle.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `momentum/trend/supertrend_follow` | Scaffold stub with `step.toml` | `honba_strategies.trend.supertrend` | `catalog/trend/supertrend_follow` | `tests/unit/trend/test_supertrend.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `momentum/breakout/volatility_breakout` | Scaffold stub with `step.toml` | `honba_strategies.trend.breakout` | `catalog/trend/volatility_breakout` | `tests/unit/trend/test_breakout.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `momentum/oscillator/momentum_oscillator`| Scaffold stub with `step.toml` | `honba_strategies.trend.oscillator` | `catalog/trend/momentum_oscillator` | `tests/unit/trend/test_oscillator.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| **`mean_reversion/`** | | | | | |
| `mean_reversion/bands/bollinger_bands` | Scaffold stub with `step.toml` | `honba_strategies.mean_reversion.bollinger_rsi` | `catalog/mean_reversion/bollinger_bands` | `tests/unit/mean_reversion/test_bollinger.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `mean_reversion/oscillator/rsi_oversold`| Scaffold stub with `step.toml` | `honba_strategies.mean_reversion.rsi` | `catalog/mean_reversion/rsi_oversold` | `tests/unit/mean_reversion/test_rsi.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `mean_reversion/oscillator/stochastic_reversion` | Scaffold stub with `step.toml` | `honba_strategies.mean_reversion.stochastic` | `catalog/mean_reversion/stochastic_reversion`| `tests/unit/mean_reversion/test_stoch.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `mean_reversion/oscillator/williams_r` | Scaffold stub with `step.toml` | `honba_strategies.mean_reversion.williams` | `catalog/mean_reversion/williams_r` | `tests/unit/mean_reversion/test_williams.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| `mean_reversion/statistical/` | Scaffold stub | `honba_strategies.mean_reversion.ornstein_uhlenbeck` | `catalog/mean_reversion/ornstein_uhlenbeck` | `tests/unit/mean_reversion/test_ou.py` | Move `step.toml` to `catalog/`; port to SDK; delete root dump |
| **`portfolio/`** | | | | | |
| `portfolio/rebalancing/equal_weight` | Working legacy strategy + tests | `honba_strategies.portfolio.equal_weight` | `catalog/portfolio/equal_weight` | `tests/unit/portfolio/test_equal_weight.py` | Move `step.toml` to `catalog/`; migrate code to SDK; delete root dump |
| **`universe/alpha/`** | | | | | |
| `universe/alpha/factor` | Scaffold stub with `step.toml` | `honba_strategies.portfolio.alpha_factors` | `catalog/portfolio/alpha30_factor` | `tests/unit/portfolio/test_factors.py` | Move `step.toml` to `catalog/`; migrate to SDK; delete root dump |
| `universe/alpha/low_vol` | Scaffold stub with `step.toml` | `honba_strategies.portfolio.alpha_factors` | `catalog/portfolio/alpha_low_vol` | `tests/unit/portfolio/test_factors.py` | Move `step.toml` to `catalog/`; migrate to SDK; delete root dump |
| `universe/alpha/mean_reversion` | Scaffold stub with `step.toml` | `honba_strategies.portfolio.alpha_factors` | `catalog/portfolio/alpha_mean_reversion` | `tests/unit/portfolio/test_factors.py` | Move `step.toml` to `catalog/`; migrate to SDK; delete root dump |
| `universe/alpha/momentum` | Scaffold stub with `step.toml` | `honba_strategies.portfolio.alpha_factors` | `catalog/portfolio/alpha_momentum` | `tests/unit/portfolio/test_factors.py` | Move `step.toml` to `catalog/`; migrate to SDK; delete root dump |
| `universe/alpha/quality` | Scaffold stub with `step.toml` | `honba_strategies.portfolio.alpha_factors` | `catalog/portfolio/alpha_quality` | `tests/unit/portfolio/test_factors.py` | Move `step.toml` to `catalog/`; migrate to SDK; delete root dump |
| **`etf/`** | | | | | |
| `etf/gold_equity_rotation` | 37-byte scaffold stub | `honba_strategies.etf_funds.rotation` | `catalog/etf_funds/gold_equity_rotation` | `tests/unit/etf_funds/test_rotation.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `etf/international_diversification` | 37-byte scaffold stub | `honba_strategies.etf_funds.rotation` | `catalog/etf_funds/international_div` | `tests/unit/etf_funds/test_rotation.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `etf/sector_rotation` | 37-byte scaffold stub | `honba_strategies.etf_funds.rotation` | `catalog/etf_funds/sector_rotation` | `tests/unit/etf_funds/test_rotation.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `etf/tracking_error_arb` | 37-byte scaffold stub | `honba_strategies.etf_funds.tracking_arb` | `catalog/etf_funds/tracking_error_arb` | `tests/unit/etf_funds/test_tracking_arb.py`| Port to SDK class; generate `catalog/` entry; delete root dump |
| **`intraday/`** | | | | | |
| `intraday/gap_fill` | 37-byte scaffold stub | `honba_strategies.intraday.gap_fill` | `catalog/intraday/gap_fill` | `tests/unit/intraday/test_gap_fill.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `intraday/opening_range_breakout` | 37-byte scaffold stub | `honba_strategies.intraday.orb` | `catalog/intraday/opening_range_breakout` | `tests/unit/intraday/test_orb.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `intraday/pivot_bounce` | 37-byte scaffold stub | `honba_strategies.intraday.pivot_bounce` | `catalog/intraday/pivot_bounce` | `tests/unit/intraday/test_pivot_bounce.py`| Port to SDK class; generate `catalog/` entry; delete root dump |
| `intraday/vwap_scalp` | 37-byte scaffold stub | `honba_strategies.intraday.vwap_scalp` | `catalog/intraday/vwap_scalp` | `tests/unit/intraday/test_vwap_scalp.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| **`mutual_funds/`** | | | | | |
| `mutual_funds/category_rotation` | 37-byte scaffold stub | `honba_strategies.etf_funds.mf_rotation` | `catalog/etf_funds/mf_category_rotation` | `tests/unit/etf_funds/test_mf.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `mutual_funds/expense_ratio_arb` | 37-byte scaffold stub | `honba_strategies.etf_funds.mf_arb` | `catalog/etf_funds/mf_expense_arb` | `tests/unit/etf_funds/test_mf.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `mutual_funds/nav_momentum` | 37-byte scaffold stub | `honba_strategies.etf_funds.mf_momentum` | `catalog/etf_funds/mf_nav_momentum` | `tests/unit/etf_funds/test_mf.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `mutual_funds/sip_optimizer` | 37-byte scaffold stub | `honba_strategies.etf_funds.sip` | `catalog/etf_funds/mf_sip_optimizer` | `tests/unit/etf_funds/test_mf.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| **`swing/`** | | | | | |
| `swing/earnings_momentum` | 37-byte scaffold stub | `honba_strategies.trend.earnings` | `catalog/trend/earnings_momentum` | `tests/unit/trend/test_earnings.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `swing/relative_strength` | 37-byte scaffold stub | `honba_strategies.trend.relative_strength` | `catalog/trend/relative_strength` | `tests/unit/trend/test_rs.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| `swing/sector_leadership` | 37-byte scaffold stub | `honba_strategies.trend.sector_leadership` | `catalog/trend/sector_leadership` | `tests/unit/trend/test_sector.py` | Port to SDK class; generate `catalog/` entry; delete root dump |
| **`ai_generated/`** | Obsolete empty directory | Purged | Purged | Purged | Delete entirely from repository |

---

## 4. SDK Ergonomics & Developer Experience

### 4.1 Direct Programmatic SDK Usage
```python
from decimal import Decimal
from honba_strategies.execution import TwapStrategy, TwapConfig

config = TwapConfig(
    symbol="RELIANCE",
    total_quantity=Decimal("1500"),
    duration_minutes=30,
    slices=15,
    randomize_jitter_pct=0.05,
    max_freeze_slice=Decimal("1800"),
)
strategy = TwapStrategy(config)
```

### 4.2 Statistical Arbitrage SDK Usage
```python
from decimal import Decimal
from honba_strategies.arbitrage import PairsTradingStrategy, PairsTradingConfig

config = PairsTradingConfig(
    symbol_a="HDFCBANK",
    symbol_b="ICICIBANK",
    lookback_window=60,
    z_score_entry=Decimal("2.0"),
    z_score_exit=Decimal("0.0"),
    z_score_stop=Decimal("3.5"),
    max_capital_per_leg=Decimal("500000"),
)
strategy = PairsTradingStrategy(config)
```

### 4.3 Composable Strategy Pipeline
```python
from decimal import Decimal
from honba_strategies.trend import TrendStrategy
from honba_strategies.components.signals import DonchianBreakoutSignal
from honba_strategies.components.sizers import AtrVolatilitySizer
from honba_strategies.components.risk import MisIntradayRiskGuard

strategy = TrendStrategy(
    signal=DonchianBreakoutSignal(period=20),
    sizer=AtrVolatilitySizer(risk_fraction=Decimal("0.02")),
    risk=MisIntradayRiskGuard(square_off_time="15:20:00"),
)
```

### 4.4 Dynamic Strategy Discovery & Catalog Bridge
```python
import honba_strategies as hs

# Introspect available SDK strategies
arbitrage_algos = hs.list_strategies(category="arbitrage")

# Instantiate by registry name with type-validated parameters
strategy = hs.create_strategy("pairs_trading", leg_a="HDFCBANK", leg_b="ICICIBANK", z_score=2.0)
```

### 4.5 CLI Experience
```bash
# List all registered production strategies
honba-strategies list

# List strategies filtered by category
honba-strategies list --category execution

# Validate catalog step manifests and chaining rules
honba-strategies catalog validate

# Inspect strategy parameter bounds and metadata
honba-strategies info twap
```

---

## 5. Phase-by-Phase Implementation & Restructuring Roadmap

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      RESTRUCTURING ROADMAP STATUS                      │
 ├────────────────────────────────────────────────────────────────────────┤
 │ Phase 0: Python SDK Packaging & Core Framework       │ ✅ COMPLETED    │
 │ Phase 1: Smart Execution & Slicing SDK (TWAP, VWAP)  │ ✅ COMPLETED    │
 │ Phase 2: Arbitrage & Relative Value SDK (Pairs, etc) │ ✅ COMPLETED    │
 │ Phase R: Source Code Restructure & Dump Elimination  │ 🚀 ACTIVE       │
 │ Phase 3: High-Frequency Market Making & Quoting SDK  │ ⏳ PLANNED      │
 │ Phase 4: Trend Following & Breakout SDK              │ ⏳ PLANNED      │
 │ Phase 5: Mean Reversion & Statistical Physics SDK    │ ⏳ PLANNED      │
 │ Phase 6: Portfolio Allocation & Dynamic Rebalancing  │ ⏳ PLANNED      │
 │ Phase 7: Options & Volatility Trading SDK            │ ⏳ PLANNED      │
 │ Phase 8: Composable Building Blocks (Signals/Sizers) │ ⏳ PLANNED      │
 │ Phase 9: Verification, StockSharp Parity & Benchmarks│ ⏳ PLANNED      │
 └────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 0: Python SDK Packaging & Core Framework (M0) — Week 1 ✅ COMPLETED
> Laying down the professional Python SDK foundation, packaging standards, and deduplication contracts.

- [x] **0.1 Modern Packaging Setup (`pyproject.toml`)**
  - [x] Configure PEP 621 metadata, `src`-layout packaging, dependencies (`honba>=0.1.0`, `scipy>=1.12`, `pydantic>=2.0`).
  - [x] Add optional dependency extras: `dev` (`pytest`, `ruff`, `mypy`), `optimization` (`cvxpy`).
  - [x] Add `py.typed` marker for PEP 561 compliance.
- [x] **0.2 Core Type System & Error Hierarchy (`honba_strategies.core`)**
  - [x] Define `StrategyConfig` base with validation and serialization (TOML/JSON roundtrip).
  - [x] Define structured exception hierarchy: `HonbaStrategyError`, `ConfigValidationError`, `RiskLimitExceededError`, `RegimeNotSupportedError`.
- [x] **0.3 Strategy Registry & Discovery Engine (`honba_strategies.core.registry`)**
  - [x] Implement `StrategyRegistry` with `@register_strategy` decorator.
  - [x] Provide factory methods `hs.get_strategy(name)` and `hs.list_strategies()`.\
  - [x] Build bridge between `registry.json` / `step.toml` and SDK classes to eliminate dual-source drift.
- [x] **0.4 Deduplication & Contract Verification with `honba` Core**
  - [x] Verify clean inheritance from `honba.strategies.base` (`SlicingStrategy`, `QuotingStrategy`, `ArbitrageStrategy`, `RebalancingStrategy`).
  - [x] Ensure all price/qty computations strictly consume `honba-core` Decimal contracts.

---

### Phase 1: Smart Execution & Slicing SDK (StockSharp Port) (M1) — Week 2–3 ✅ COMPLETED
> Porting StockSharp execution algorithms as high-performance, parameter-driven SDK classes.

- [x] **1.1 TWAP Execution Strategy (`TwapStrategy`)**
  - [x] Inherit from `honba.strategies.base.SlicingStrategy`.
  - [x] Divide large parent order into $N$ equal slices across duration with randomized microsecond time jitter.
  - [x] Integrate SEBI single-order freeze limit slicing (e.g. NIFTY max 1,800 contracts).
  - [x] Expose declarative parameters: `total_quantity`, `duration_minutes`, `slice_count`, `jitter_pct`.
- [x] **1.2 VWAP Execution Strategy (`VwapStrategy`)**
  - [x] Dynamic slice sizing proportional to historical exchange intraday volume curve (NSE 09:15–15:30 profile).
  - [x] Real-time pace adjustment based on accumulated volume and participation target.
  - [x] Expose declarative parameters: `target_volume_pct`, `start_time`, `end_time`, `urgency`.
- [x] **1.3 Percentage of Volume (POV) Slicer (`PovStrategy`)**
  - [x] Dynamic execution tracking a continuous target participation rate (e.g. 5% or 10% of market volume).
  - [x] Dynamic speed-up during liquidity bursts and automatic pause during order book droughts.
- [x] **1.4 Synthetic Iceberg Slicer (`IcebergStrategy`)**
  - [x] Maintain working visible quote while withholding hidden remainder in local order manager.
  - [x] Automatically replenish visible leg upon fill with randomized display variance to prevent adverse detection.

---

### Phase 2: Arbitrage & Relative Value SDK (StockSharp Port) (M2) — Week 4–5 ✅ COMPLETED
> Porting StockSharp arbitrage engines for risk-neutral spread extraction across Indian markets.

- [x] **2.1 Statistical Arbitrage & Pairs Trading (`PairsTradingStrategy`)**
  - [x] Inherit from `honba.strategies.base.ArbitrageStrategy`.
  - [x] Engle-Granger and Johansen cointegration testing module for asset pair validation.
  - [x] Real-time spread tracking: $S_t = \ln(P_{A, t}) - \beta \ln(P_{B, t}) - \alpha$.
  - [x] Dynamic rolling z-score entry ($Z \ge 2.0$), stop-loss ($Z \ge 3.5$), and mean exit ($Z = 0.0$).
  - [x] Atomic two-leg execution with leg-risk timeout mitigation.
- [x] **2.2 Cash-and-Carry Basis Arbitrage (`CashAndCarryStrategy`)**
  - [x] Real-time ingestion of spot equity (NSE) and near-month equity futures (NFO).
  - [x] Mispricing detector accounting for financing rate + statutory taxes (STT, GST, Stamp Duty).
  - [x] Long delivery equity (`CNC`), short near-month future; hold until expiry settlement at parity.
- [x] **2.3 Index & ETF Basket Arbitrage (`BasketArbitrageStrategy`)**
  - [x] Monitor spread between NIFTY 50 ETF (e.g. NIFTYBEES) and synthetic basket of underlying 50 scrips.
  - [x] Execute synchronized basket creation/redemption arbitrage on persistent mispricings.

---

### Phase R: Source Code Restructuring & Dump Elimination (Immediate Priority) ✅ COMPLETED
> Transforming the repository from a fragmented file dump into a clean, professional, 4-zone production architecture.

- [x] **R.1 Test Suite Consolidation & Config Unification**
  - [x] Move root test files into `tests/catalog/`:
    - `test_registry.py` -> `tests/catalog/test_registry.py`
    - `test_step_manifests.py` -> `tests/catalog/test_step_manifests.py`
    - `test_step_chain.py` -> `tests/catalog/test_step_chain.py`
    - `test_catalog_fills.py` -> `tests/catalog/test_catalog_fills.py`
    - `test_readme_sections.py` -> `tests/catalog/test_readme_sections.py`
  - [x] Move `conftest.py` to `tests/conftest.py` with automatic repository root and `tools/` path inclusion.
  - [x] Delete `pytest.ini` at repository root; consolidate all pytest configurations into `pyproject.toml` under `[tool.pytest.ini_options]` (`testpaths = ["tests"]`).
  - [x] Validate `pytest` execution runs cleanly from root with zero collection errors.
- [x] **R.2 Catalog Migration & Registry Normalization**
  - [x] Move all viable `step.toml`, `config.toml`, `README.md` manifests from root dump folders into their canonical `catalog/<category>/<strategy_name>/` paths:
    - `momentum/trend/*` -> `catalog/trend/*` (removed, not yet implemented)
    - `momentum/breakout/*` -> `catalog/trend/*` (removed, not yet implemented)
    - `momentum/oscillator/*` -> `catalog/trend/*` (removed, not yet implemented)
    - `mean_reversion/bands/*` -> `catalog/mean_reversion/*` (removed, not yet implemented)
    - `mean_reversion/oscillator/*` -> `catalog/mean_reversion/*` (removed, not yet implemented)
    - `portfolio/rebalancing/*` -> `catalog/portfolio/*` (removed, not yet implemented)
    - `universe/alpha/*` -> `catalog/portfolio/*` (removed, not yet implemented)
  - [x] Standardize catalog wrappers: create minimal `strategy.py` files in each catalog folder importing from `honba_strategies`.
  - [x] Update `registry.json` so 100% of strategy paths point strictly to `catalog/...` (eliminating all legacy root paths).
  - [x] Update catalog test assertions to validate solely against `catalog/`.
- [x] **R.3 Complete Purge of Root Dump Folders**
  - [x] Permanently remove legacy root dump folders:
    `rm -rf etf/ intraday/ mean_reversion/ momentum/ mutual_funds/ options/ portfolio/ swing/ ai_generated/ universe/`
  - [x] Remove root test scripts:
    `rm -f test_catalog_fills.py test_readme_sections.py test_registry.py test_step_chain.py test_step_manifests.py`
  - [x] Purge root `pytest.ini` and leftover `.pyc` caches.
  - [x] Confirm `git status` displays a pristine root matching Section 2.2.
- [x] **R.4 Python SDK Subpackage Structure Finalization**
  - [x] Ensure all SDK domain packages in `src/honba_strategies/` contain valid `__init__.py` and public exports:
    - `core/` (Base classes, configuration, error hierarchy, registry)
    - `execution/` (TWAP, VWAP, POV, Iceberg)
    - `arbitrage/` (Pairs, Cash-and-Carry, Basket Arbitrage)
    - `market_making/` (Avellaneda-Stoikov, Spread Quoting, Ladder)
    - `trend/` (Turtle, KAMA, Supertrend, Breakout) - placeholder
    - `mean_reversion/` (Bollinger-RSI, VWAP Bands, Ornstein-Uhlenbeck) - placeholder
    - `portfolio/` (Equal Weight, Risk Parity, Markowitz, Alpha Factors) - placeholder
    - `options/` (Short Straddle, Iron Condor, Covered Call, Calendar) - placeholder
    - `etf_funds/` (Asset Rotation, Tracking Error Arbitrage) - placeholder
    - `intraday/` (Gap Fill, ORB, Pivot Bounce) - placeholder
    - `components/` (`signals/`, `sizers/`, `risk/`) - placeholder
    - `cli.py`
  - [x] Update top-level `src/honba_strategies/__init__.py` to export all canonical classes and version metadata.
- [x] **R.5 Verification Gates**
  - [x] `pytest tests/` passes 100% (unit, integration, and catalog suites).
  - [x] `ruff check .` passes with zero linting errors.
  - [ ] `mypy` runs in strict mode without typing violations.

---

### Phase 3: High-Frequency Market Making & Quoting SDK (StockSharp Port) (M3) — Week 6–7 ✅ COMPLETED
> Porting StockSharp quoting algorithms for automated liquidity provision.

- [x] **3.1 Passive Spread Quoting (`SpreadQuotingStrategy`)**
  - [x] Implement in `src/honba_strategies/market_making/spread.py`, inheriting from `honba.strategies.base.QuotingStrategy`.
  - [x] Place continuous bid at Best Bid and ask at Best Ask with automated cancel-replace on price drift.
  - [x] Guard against adverse selection using Order Book Imbalance (OBI) indicator from `honba-me`.
  - [x] Add catalog entry in `catalog/market_making/spread_quoting/` and unit tests in `tests/unit/market_making/test_spread.py`.
- [x] **3.2 Avellaneda-Stoikov Market Maker (`AvellanedaStoikovStrategy`)**
  - [x] Implement in `src/honba_strategies/market_making/avellaneda_stoikov.py`.
  - [x] Compute reservation price based on inventory risk aversion parameter $\gamma$:
    $$R(s, q, t) = s - q \gamma \sigma^2 (T - t)$$
  - [x] Dynamic asymmetric quoting: lower bid and widen ask when net long; raise bid and tighten ask when short.
  - [x] Dynamic half-spread calculation: $r(s, q, t) + \frac{1}{\gamma} \ln(1 + \frac{\gamma}{\kappa})$.
  - [x] Add catalog entry in `catalog/market_making/avellaneda_stoikov/` and unit tests.
- [x] **3.3 Multi-Level Ladder Quoting (`LadderQuotingStrategy`)**
  - [x] Implement in `src/honba_strategies/market_making/ladder.py`.
  - [x] Multi-tier grid quoting across $L$ depth levels with geometric size decay.
  - [x] Inventory-aware queue position tracking and layer rebalancing.
  - [x] Add catalog entry in `catalog/market_making/ladder_quoting/` and unit tests.

---

### Phase 4: Trend Following & Breakout SDK (StockSharp Port) (M4) — Week 8–9 ✅ COMPLETED
> Porting StockSharp classic and adaptive trend following systems.

- [x] **4.1 Turtle Trading System (`TurtleStrategy`)**
  - [x] Implement in `src/honba_strategies/trend/turtle.py`.
  - [x] Classical Richard Dennis 20-day (System 1) and 55-day (System 2) Donchian breakout channels.
  - [x] Volatility-normalized position sizing based on 20-day ATR ($N$).
  - [x] Pyramiding logic: add 1 unit every $0.5N$ profit up to 4 units; hard stop at $2N$ from last entry.
  - [x] Add catalog entry in `catalog/trend/turtle_20/` and unit tests in `tests/unit/trend/test_turtle.py`.
- [x] **4.2 Adaptive Moving Average Crossover (`KamaCrossoverStrategy`)**
  - [x] Implement in `src/honba_strategies/trend/kama.py`.
  - [x] Dual KAMA (Kaufman Adaptive Moving Average) adapting to the market Efficiency Ratio (ER).
  - [x] Suppress whipsaw signals during sideways consolidation; react sharply during fast regime shifts.
  - [x] Add catalog entry in `catalog/trend/kama_crossover/` and unit tests in `tests/unit/trend/test_kama.py`.
- [x] **4.3 Multi-Timeframe Supertrend (`SupertrendStrategy`)**
  - [x] Implement in `src/honba_strategies/trend/supertrend.py`.
  - [x] Higher-timeframe (1-hour) trend direction filter combined with lower-timeframe (5-minute) ATR trailing stops.
  - [x] Add catalog entry in `catalog/trend/supertrend_follow/` and unit tests.

---

### Phase 5: Mean Reversion & Statistical Physics SDK (StockSharp Port) (M5) — Week 10–11
> Porting StockSharp statistical and volatility-envelope mean reversion algorithms.

- [ ] **5.1 Bollinger Band + RSI Exhaustion (`BollingerRsiStrategy`)**
  - [ ] Implement in `src/honba_strategies/mean_reversion/bollinger_rsi.py`.
  - [ ] Long entry when price closes below Lower Bollinger Band ($2\sigma$) and RSI $< 25$.
  - [ ] Exit on reversion to Middle Band (20 SMA) or opposite band touch.
  - [ ] Add catalog entry in `catalog/mean_reversion/bollinger_rsi/` and unit tests.
- [ ] **5.2 Intraday VWAP Band Reversion (`VwapBandReversionStrategy`)**
  - [ ] Implement in `src/honba_strategies/mean_reversion/vwap_bands.py`.
  - [ ] Intraday mean reversion when price deviates $\ge 2.5\sigma$ from session VWAP.
  - [ ] Strict 15:20 IST auto-square-off enforcement for MIS equity.
  - [ ] Add catalog entry in `catalog/mean_reversion/vwap_bands/` and unit tests.
- [ ] **5.3 Ornstein-Uhlenbeck Mean Reversion (`OuMeanReversionStrategy`)**
  - [ ] Implement in `src/honba_strategies/mean_reversion/ornstein_uhlenbeck.py`.
  - [ ] Fits continuous-time Ornstein-Uhlenbeck stochastic process:
    $$dX_t = \theta (\mu - X_t) dt + \sigma dW_t$$
  - [ ] Computes exact half-life of mean reversion ($t_{1/2} = \frac{\ln 2}{\theta}$) and trades only scrips with $t_{1/2} < 5$ days.
  - [ ] Add catalog entry in `catalog/mean_reversion/ornstein_uhlenbeck/` and unit tests.

---

### Phase 6: Portfolio Allocation & Dynamic Rebalancing SDK (StockSharp Port) (M6) — Week 12–13
> Porting StockSharp portfolio management and asset allocation models.

- [ ] **6.1 Equal Weight & Periodic Rebalancer (`EqualWeightRebalancer`)**
  - [ ] Implement in `src/honba_strategies/portfolio/equal_weight.py`, inheriting from `honba.strategies.base.RebalancingStrategy`.
  - [ ] Target weight allocations across universe with configurable drift threshold bands (e.g. $\pm 5\%$).
  - [ ] Transaction cost aware rebalancing threshold gate.
  - [ ] Add catalog entry in `catalog/portfolio/equal_weight/` and unit tests.
- [ ] **6.2 Risk Parity Allocation (`RiskParityStrategy`)**
  - [ ] Implement in `src/honba_strategies/portfolio/risk_parity.py`.
  - [ ] Weight assets inversely proportional to their historical volatility matrix so each asset contributes equal risk.
  - [ ] Add catalog entry in `catalog/portfolio/risk_parity/` and unit tests.
- [ ] **6.3 Mean-Variance Markowitz Optimizer (`MarkowitzStrategy`)**
  - [ ] Implement in `src/honba_strategies/portfolio/markowitz.py`.
  - [ ] Quadratic optimization maximizing Sharpe ratio subject to minimum/maximum weight and sector bounds.
  - [ ] Add catalog entry in `catalog/portfolio/markowitz/` and unit tests.
- [ ] **6.4 Alpha Factor Portfolios (`AlphaFactorStrategy`)**
  - [ ] Implement in `src/honba_strategies/portfolio/alpha_factors.py`.
  - [ ] Multi-factor portfolio scoring (Momentum, Low Vol, Quality, Value) across NSE indices (NIFTY 200, NIFTY 500).
  - [ ] Add catalog entries in `catalog/portfolio/alpha30_factor/`, `catalog/portfolio/alpha_low_vol/`, etc.

---

### Phase 7: Options & Volatility Trading SDK (M7) — Week 14
> Production Indian options strategies with Greeks management, margin awareness, and time-decay harvesting.

- [ ] **7.1 ATM Short Straddle with Dynamic Hedging (`ShortStraddleStrategy`)**
  - [ ] Implement in `src/honba_strategies/options/straddle.py`.
  - [ ] Synchronized short ATM Call + ATM Put execution on NIFTY/BANKNIFTY indices.
  - [ ] Individual leg stop-loss (e.g. 25% premium expansion) with combined MTM stop-loss.
  - [ ] Add catalog entry in `catalog/options/nifty_short_straddle/` and unit tests.
- [ ] **7.2 Iron Condor Range-Bound Volatility Capture (`IronCondorStrategy`)**
  - [ ] Implement in `src/honba_strategies/options/iron_condor.py`.
  - [ ] 4-leg defined risk structure: short OTM credit spread (call + put) flanked by long wing protection.
  - [ ] Dynamic delta-neutral wing adjustment and early profit take (50% max profit).
  - [ ] Add catalog entry in `catalog/options/banknifty_iron_condor/` and unit tests.
- [ ] **7.3 Covered Call Dividend & Yield Engine (`CoveredCallStrategy`)**
  - [ ] Implement in `src/honba_strategies/options/covered_call.py`.
  - [ ] Synthesizes cash delivery long stock (`CNC`) with rolling OTM call option writing.
  - [ ] Assignment protection and strike rollover rules before expiry settlement.
  - [ ] Add catalog entry in `catalog/options/covered_call/` and unit tests.

---

### Phase 8: Composable Building Blocks (Signals, Sizers, Risk Guards) (M8) — Week 15
> Breaking strategies into modular, reusable components for flexible quantitative research.

- [ ] **8.1 Reusable Alpha Signal Generators (`honba_strategies.components.signals`)**
  - [ ] Cointegration spread signal (`CointegrationSignal`).
  - [ ] Ornstein-Uhlenbeck stochastic fit signal (`OrnsteinUhlenbeckSignal`).
  - [ ] Donchian channel breakout signal (`DonchianBreakoutSignal`).
- [ ] **8.2 Reusable Position Sizing Engines (`honba_strategies.components.sizers`)**
  - [ ] ATR-normalized volatility sizer (`AtrVolatilitySizer`).
  - [ ] Kelly Criterion optimal fraction sizer (`KellySizer`).
  - [ ] Equal risk contribution sizer (`EqualRiskSizer`).
- [ ] **8.3 Indian Regulatory & Microstructure Risk Guards (`honba_strategies.components.risk`)**
  - [ ] SEBI Algo ID enforcement guard (`SebiAlgoIdGuard`).
  - [ ] Order-to-Trade Ratio (OTR) throttling guard (`OtrThrottleGuard`).
  - [ ] Intraday MIS 15:20 IST square-off guard (`MisSquareOffGuard`).
  - [ ] Circuit band & price band lock guard (`CircuitBandGuard`).

---

### Phase 9: Verification, StockSharp Parity & Benchmark Suite (M9) — Week 16
> Ensuring institutional fidelity, numeric accuracy, and complete clean repository status.

- [ ] **9.1 Test Suite & Coverage**
  - [ ] 100% pass rate across `pytest tests/` for SDK modules, components, and catalog entries.
  - [ ] Delayed fill tests (`tests/catalog/test_catalog_fills.py`) ensuring zero duplicate orders across all execution modes.
- [ ] **9.2 Golden Vector Parity against StockSharp C#**
  - [ ] Benchmark trade signals, reservation prices, and slicing schedules against StockSharp C# reference implementations.
  - [ ] Zero decimal discrepancy on accounting calculations.
- [ ] **9.3 Indian Market Stress Testing in `honba-ya-backtest`**
  - [ ] 5-year historical backtesting across NSE/NFO universe with exact statutory taxes and slippage models.
  - [ ] Verification of DSR (Deflated Sharpe Ratio) and PBO (Probability of Backtest Overfitting).
