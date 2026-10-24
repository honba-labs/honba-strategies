# Master Plan: 本場・策 honba-strategies (Python Strategy SDK)

> **The production quantitative strategy SDK and algorithmic catalog for the Honba platform.**  
> Houses battle-tested algorithmic trading strategies, institutional execution algorithms, statistical arbitrage models, high-frequency quoting engines, and dynamic portfolio rebalancers ported from **StockSharp (`StockSharp.Algo.Strategies`)** and modernized for Indian financial markets (NSE, BSE, NFO, MCX) and global multi-asset trading.  
> Packaged as a standard, typed, pip-installable Python SDK (`honba-strategies`), powered by the compiled Rust kernel (`honba-core` / `honba-tamashii`), 100% exact 128-bit decimal arithmetic, and strict research-live parity.

---

## 0. Executive Summary & SDK Architectural Vision

StockSharp provides one of the industry's most battle-tested algorithmic trading libraries in C#. Meanwhile, modern quantitative research and production trading demand **Python-first ergonomics**, **strict type safety**, **modular composability**, and **seamless research-to-live parity**.

`honba-strategies` bridges this gap as a dual-surface system:
1. **Pip-Installable Python SDK (`honba_strategies`)**: A clean, modular Python library providing concrete, production-grade strategy implementations and composable components (`signals`, `sizers`, `risk`, `execution`).
2. **Declarative Strategy Catalog (`registry.json`, `step.toml`)**: A structured catalog indexing strategies with parameter bounds, input/output contracts, and UI schemas for visual strategy chaining and automated execution.

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
- **PEP 517 / PEP 621 Packaging**: Standard `pyproject.toml` using `setuptools` (with `find_packages`) or `hatchling`.
- **`src`-Layout**: Source code isolated under `src/honba_strategies/` to guarantee import parity between development checkouts and installed wheels.
- **Strict Typing (PEP 561)**: Includes `py.typed` marker; passes `pyright` and `mypy` in strict mode with 100% typed public APIs.
- **Structured Configuration**: Parameter schemas defined via declarative `Parameter` descriptors and validated via typed config dataclasses/Pydantic models.
- **Exact Decimal Arithmetic**: 100% exact price, quantity, and cash accounting using `Decimal` / `rust_decimal`. Floats are confined strictly to statistical metrics (z-scores, half-life, correlations, Greeks).

### 1.3 First-Class Indian Market Microstructure
- **SEBI & Exchange Conformance**: Dynamic single-order freeze limit slicing (e.g. NIFTY 1,800 contracts), Order-to-Trade Ratio (OTR) safety margins, mandatory SEBI Algo ID tagging, and scrip operational circuit bands.
- **Intraday & Settlement Realities**: Automatic MIS 15:20 IST square-off enforcement, T+1 Demat settlement calendar awareness, and statutory cost accounting (STT, GST, Stamp Duty, Exchange Turnover fees).

---

## 2. Target Directory & Package Structure

```text
honba-strategies/
├── pyproject.toml                     # PEP 621 build & package metadata
├── README.md                          # SDK user guide, quickstart & catalog docs
├── registry.json                      # Catalog index for UI/CLI strategy discovery
├── schema/
│   ├── step.schema.json               # JSON Schema for declarative step manifests
│   └── README.md                      # Chaining rules & schema specification
├── src/
│   └── honba_strategies/              # The importable Python SDK package
│       ├── __init__.py                # Top-level exports & __version__ = "0.1.0"
│       ├── py.typed                   # PEP 561 typing marker
│       ├── core/                      # SDK foundation & base extensions
│       │   ├── __init__.py
│       │   ├── config.py              # Base strategy configuration & validation
│       │   ├── errors.py              # Strategy exceptions hierarchy
│       │   └── registry.py            # SDK StrategyRegistry & @register_strategy decorator
│       ├── execution/                 # Institutional Slicing & Execution (StockSharp Port)
│       │   ├── __init__.py            # TwapStrategy, VwapStrategy, PovStrategy, IcebergStrategy
│       │   ├── twap.py                # TWAP with microsecond jitter & freeze slicing
│       │   ├── vwap.py                # Volume profile VWAP tracking & pace adjust
│       │   ├── pov.py                 # Percentage of Volume dynamic participation
│       │   └── iceberg.py             # Synthetic iceberg display & replenish
│       ├── arbitrage/                 # Relative Value & Arbitrage (StockSharp Port)
│       │   ├── __init__.py            # PairsTradingStrategy, CashAndCarryStrategy, BasketArbitrageStrategy
│       │   ├── pairs.py               # Cointegration & z-score dual-leg pairs trading
│       │   ├── cash_and_carry.py      # Spot vs near-month future statutory basis arbitrage
│       │   └── basket.py              # Index ETF vs synthetic basket creation/redemption
│       ├── market_making/             # High-Frequency Liquidity Provision (StockSharp Port)
│       │   ├── __init__.py            # AvellanedaStoikovStrategy, SpreadQuotingStrategy, LadderQuotingStrategy
│       │   ├── avellaneda_stoikov.py  # Inventory-risk reservation price quoting
│       │   ├── spread.py              # Best bid/ask pegging with order book imbalance skew
│       │   └── ladder.py              # Multi-tier grid quoting with inventory decay
│       ├── trend/                     # Trend Following & Breakout (StockSharp Port)
│       │   ├── __init__.py            # TurtleStrategy, KamaCrossoverStrategy, SupertrendStrategy
│       │   ├── turtle.py              # Richard Dennis Donchian breakout & N-ATR pyramiding
│       │   ├── kama.py                # Kaufman Adaptive Moving Average noise-filtered cross
│       │   └── supertrend.py          # Multi-timeframe ATR trailing breakout
│       ├── mean_reversion/            # Statistical & Volatility Mean Reversion (StockSharp Port)
│       │   ├── __init__.py            # BollingerRsiStrategy, VwapBandReversionStrategy, OuReversionStrategy
│       │   ├── bollinger_rsi.py       # Bollinger envelope deviation + RSI exhaustion
│       │   ├── vwap_bands.py          # Session VWAP 2.5σ intraday mean reversion
│       │   └── ornstein_uhlenbeck.py  # Continuous-time OU stochastic process mean reversion
│       ├── portfolio/                 # Dynamic Allocation & Rebalancing (StockSharp Port)
│       │   ├── __init__.py            # EqualWeightRebalancer, RiskParityStrategy, MarkowitzStrategy
│       │   ├── equal_weight.py        # Drift-band periodic rebalancer
│       │   ├── risk_parity.py         # Equal risk contribution inverse-volatility allocation
│       │   └── markowitz.py           # Mean-variance quadratic optimization with sector bounds
│       ├── components/                # Reusable Strategy Building Blocks
│       │   ├── __init__.py
│       │   ├── signals/               # Alpha & technical signals (OU-fit, cointegration, z-scores)
│       │   ├── sizers/                # Position sizers (ATR volatility sizing, Kelly, target risk)
│       │   └── risk/                  # Indian risk guards (OTR monitor, drawdown halt, MIS square-off)
│       └── testing/                   # Test utilities, synthetic book replay, golden vector runners
├── catalog/                           # Declarative Catalog Manifests & Metadata
│   ├── execution/                     # Twap, Vwap, Pov, Iceberg step.toml & config.toml
│   ├── arbitrage/                     # Pairs, Cash-and-carry step.toml & config.toml
│   ├── market_making/                 # Quoting step.toml & config.toml
│   ├── trend/                         # Turtle, Kama step.toml & config.toml
│   ├── mean_reversion/                # Bollinger, VWAP band step.toml & config.toml
│   └── portfolio/                     # Equal weight, risk parity step.toml & config.toml
└── tests/                             # Comprehensive test suite
    ├── unit/                          # Isolated strategy & component unit tests
    ├── integration/                   # Delayed fill replay & lifecycle tests
    ├── parity/                        # Golden vector comparisons against StockSharp C#
    └── catalog/                       # Registry, manifest schema & step chain tests
```

---

## 3. SDK Ergonomics & Developer Experience

### 3.1 Direct Programmatic SDK Usage
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

### 3.2 Composable Strategy Pipeline
```python
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

### 3.3 Dynamic Strategy Discovery & Catalog Bridge
```python
import honba_strategies as hs

# Introspect available SDK strategies
arbitrage_algos = hs.list_strategies(category="arbitrage")

# Instantiate by registry name with type-validated parameters
strategy = hs.create("pairs_trading", leg_a="HDFCBANK", leg_b="ICICIBANK", z_score=2.0)
```

---

## 4. Phase-by-Phase Implementation Roadmap

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
  - [x] Provide factory methods `hs.get_strategy(name)` and `hs.list_strategies()`.
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

### Phase 3: High-Frequency Market Making & Quoting SDK (StockSharp Port) (M3) — Week 6–7
> Porting StockSharp quoting algorithms for automated liquidity provision.

- [ ] **3.1 Passive Spread Quoting (`SpreadQuotingStrategy`)**
  - [ ] Inherit from `honba.strategies.base.QuotingStrategy`.
  - [ ] Place continuous bid at Best Bid and ask at Best Ask with automated cancel-replace on price drift.
  - [ ] Guard against adverse selection using Order Book Imbalance (OBI) indicator from `honba-me`.
- [ ] **3.2 Avellaneda-Stoikov Market Maker (`AvellanedaStoikovStrategy`)**
  - [ ] Compute reservation price based on inventory risk aversion parameter $\gamma$:
    $$R(s, q, t) = s - q \gamma \sigma^2 (T - t)$$
  - [ ] Dynamic asymmetric quoting: lower bid and widen ask when net long; raise bid and tighten ask when short.
  - [ ] Dynamic half-spread calculation: $r(s, q, t) + \frac{1}{\gamma} \ln(1 + \frac{\gamma}{\kappa})$.
- [ ] **3.3 Multi-Level Ladder Quoting (`LadderQuotingStrategy`)**
  - [ ] Multi-tier grid quoting across $L$ depth levels with geometric size decay.
  - [ ] Inventory-aware queue position tracking and layer rebalancing.

---

### Phase 4: Trend Following & Breakout SDK (StockSharp Port) (M4) — Week 8–9
> Porting StockSharp classic and adaptive trend following systems.

- [ ] **4.1 Turtle Trading System (`TurtleStrategy`)**
  - [ ] Classical Richard Dennis 20-day (System 1) and 55-day (System 2) Donchian breakout channels.
  - [ ] Volatility-normalized position sizing based on 20-day ATR ($N$).
  - [ ] Pyramiding logic: add 1 unit every $0.5N$ profit up to 4 units; hard stop at $2N$ from last entry.
- [ ] **4.2 Adaptive Moving Average Crossover (`KamaCrossoverStrategy`)**
  - [ ] Dual KAMA (Kaufman Adaptive Moving Average) adapting to the market Efficiency Ratio (ER).
  - [ ] Suppress whipsaw signals during sideways consolidation; react sharply during fast regime shifts.
- [ ] **4.3 Multi-Timeframe Supertrend (`SupertrendStrategy`)**
  - [ ] Higher-timeframe (1-hour) trend direction filter combined with lower-timeframe (5-minute) ATR trailing stops.

---

### Phase 5: Mean Reversion & Statistical Physics SDK (StockSharp Port) (M5) — Week 10–11
> Porting StockSharp statistical and volatility-envelope mean reversion algorithms.

- [ ] **5.1 Bollinger Band + RSI Exhaustion (`BollingerRsiStrategy`)**
  - [ ] Long entry when price closes below Lower Bollinger Band ($2\sigma$) and RSI $< 25$.
  - [ ] Exit on reversion to Middle Band (20 SMA) or opposite band touch.
- [ ] **5.2 Intraday VWAP Band Reversion (`VwapBandReversionStrategy`)**
  - [ ] Intraday mean reversion when price deviates $\ge 2.5\sigma$ from session VWAP.
  - [ ] Strict 15:20 IST auto-square-off enforcement for MIS equity.
- [ ] **5.3 Ornstein-Uhlenbeck Mean Reversion (`OuMeanReversionStrategy`)**
  - [ ] Fits continuous-time Ornstein-Uhlenbeck stochastic process:
    $$dX_t = \theta (\mu - X_t) dt + \sigma dW_t$$
  - [ ] Computes exact half-life of mean reversion ($t_{1/2} = \frac{\ln 2}{\theta}$) and trades only scrips with $t_{1/2} < 5$ days.

---

### Phase 6: Portfolio Allocation & Dynamic Rebalancing SDK (StockSharp Port) (M6) — Week 12–13
> Porting StockSharp portfolio management and asset allocation models.

- [ ] **6.1 Equal Weight & Periodic Rebalancer (`EqualWeightRebalancer`)**
  - [ ] Inherit from `honba.strategies.base.RebalancingStrategy`.
  - [ ] Target weight allocations across universe with configurable drift threshold bands (e.g. $\pm 5\%$).
  - [ ] Transaction cost aware rebalancing threshold gate.
- [ ] **6.2 Risk Parity Allocation (`RiskParityStrategy`)**
  - [ ] Weight assets inversely proportional to their historical volatility matrix so each asset contributes equal risk.
- [ ] **6.3 Mean-Variance Markowitz Optimizer (`MarkowitzStrategy`)**
  - [ ] Quadratic optimization maximizing Sharpe ratio subject to minimum/maximum weight and sector bounds.

---

### Phase 7: Composable Building Blocks (Signals, Sizers, Risk Guards) (M7) — Week 14
> Breaking strategies into modular, reusable components for flexible quantitative research.

- [ ] **7.1 Reusable Alpha Signal Generators (`honba_strategies.components.signals`)**
  - [ ] Cointegration spread signal (`CointegrationSignal`).
  - [ ] Ornstein-Uhlenbeck stochastic fit signal (`OrnsteinUhlenbeckSignal`).
  - [ ] Donchian channel breakout signal (`DonchianBreakoutSignal`).
- [ ] **7.2 Reusable Position Sizing Engines (`honba_strategies.components.sizers`)**
  - [ ] ATR-normalized volatility sizer (`AtrVolatilitySizer`).
  - [ ] Kelly Criterion optimal fraction sizer (`KellySizer`).
  - [ ] Equal risk contribution sizer (`EqualRiskSizer`).
- [ ] **7.3 Indian Regulatory & Microstructure Risk Guards (`honba_strategies.components.risk`)**
  - [ ] SEBI Algo ID enforcement guard (`SebiAlgoIdGuard`).
  - [ ] Order-to-Trade Ratio (OTR) throttling guard (`OtrThrottleGuard`).
  - [ ] Intraday MIS 15:20 IST square-off guard (`MisSquareOffGuard`).
  - [ ] Circuit band & price band lock guard (`CircuitBandGuard`).

---

### Phase 8: Declarative Catalog Bridge & Step Manifest Synchronization (M8) — Week 15
> Unifying the programmatic Python SDK with the declarative visual tooling and catalog index.

- [ ] **8.1 Automatic Step Manifest (`step.toml`) Generator**
  - [ ] Introspect declared `Parameter` descriptors on SDK strategies and emit schema-compliant `step.toml` manifests.
  - [ ] Keep `registry.json`, `step.toml`, and SDK code in 100% automated synchronization.
- [ ] **8.2 Visual Strategy Chaining & Validation**
  - [ ] Validate step inputs/outputs using `schema/step.schema.json` and `tools/validate_chain.py`.
  - [ ] Ensure every SDK strategy can be embedded into multi-step pipelines.

---

### Phase 9: Verification, StockSharp Parity & Benchmark Suite (M9) — Week 16
> Ensuring institutional fidelity and numeric accuracy.

- [ ] **9.1 Test Suite & Coverage**
  - [ ] 100% pass rate across `pytest tests/` for both SDK modules and catalog entries.
  - [ ] Delayed fill tests (`test_catalog_fills.py`) ensuring zero duplicate orders across all execution modes.
- [ ] **9.2 Golden Vector Parity against StockSharp C#**
  - [ ] Benchmark trade signals, reservation prices, and slicing schedules against StockSharp C# reference implementations.
  - [ ] Zero decimal discrepancy on accounting calculations.
- [ ] **9.3 Indian Market Stress Testing in `honba-ya-backtest`**
  - [ ] 5-year historical backtesting across NSE/NFO universe with exact statutory taxes and slippage models.
  - [ ] Verification of DSR (Deflated Sharpe Ratio) and PBO (Probability of Backtest Overfitting).
