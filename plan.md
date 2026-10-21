# Master Plan: 本場・策 honba-strategies

> **The production quantitative strategy library for the Honba platform.**  
> Houses algorithmic trading strategies, execution algorithms, arbitrage models, and portfolio rebalancers ported from **StockSharp (`StockSharp.Algo.Strategies`)** and modernized for Indian financial markets (NSE, BSE, NFO, MCX) and multi-asset global trading. Implemented using the Python-First SDK (`honba`), 100% exact 128-bit decimal arithmetic, and strict research-live parity.

---

## 0. Executive Summary & StockSharp Porting Scope

StockSharp provides one of the industry's most comprehensive suites of algorithmic strategies in C#. This master plan defines the systematic port of **StockSharp.Algo.Strategies** into high-performance Python 3.12+ (powered by the compiled Rust core in `honba-tamashii` and `honba-core`):

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │              StockSharp.Algo.Strategies -> honba-strategies            │
 ├───────────────────┬────────────────────────────────────────────────────┤
 │ Market Making     │ Quoting, Avellaneda-Stoikov Spread, Depth Skew     │
 │ Arbitrage         │ Statistical Pairs, Cash-and-Carry Basis, Basket    │
 │ Smart Execution   │ TWAP, VWAP, Percentage of Volume (POV), Iceberg    │
 │ Trend & Breakout  │ Turtle Trading (Donchian), KAMA/Hull, Supertrend   │
 │ Mean Reversion    │ Bollinger + RSI Exhaustion, VWAP 2σ Bands          │
 │ Portfolio Mgmt    │ Risk Parity, Mean-Variance Markowitz, Dynamic Rebal│
 └───────────────────┴────────────────────────────────────────────────────┘
```

---

## 1. Architectural Principles

1. **Python-First Ergonomics (like NautilusTrader & Jesse)**: Strategies inherit from `honba.Strategy`, define declarative parameters using `Parameter(min=..., max=..., step=...)`, and utilize lifecycle hooks (`on_start`, `on_bar`, `on_tick`, `on_order_event`).
2. **Research-Live Parity**: The exact same strategy class executes in historical backtests (`honba-ya-backtest`), paper trading, and multi-broker live trading (`honba-te`).
3. **Exact Decimal Accounting**: All internal prices, quantities, and cash are computed using `rust_decimal::Decimal` (via Python `Decimal`). Zero floating-point rounding errors.
4. **First-Class Indian Market Microstructure**: Native handling of SEBI Algo ID tagging, Order-to-Trade Ratio (OTR) safety margins, scrip circuit bands, intraday MIS 15:20 square-off, and ICCL T+1 Demat settlement.

---

## 2. Phase-by-Phase Implementation Roadmap

### Phase 1: Smart Execution & Slicing Algos (StockSharp Port) (M0) — Week 1–2
> Porting StockSharp execution algorithms to prevent adverse market impact and comply with exchange freeze limits.

- [ ] **1.1 TWAP Execution Strategy (`TwapStrategy`)**
  - [ ] Port `StockSharp.Algo.Strategies.TwapStrategy` to Python.
  - [ ] Divide large parent order into $N$ equal slices distributed across specified execution duration.
  - [ ] Add randomized microsecond time jitter to avoid exchange algorithm detection.
  - [ ] Enforce SEBI single-order freeze limit slicing (e.g. NIFTY max 1,800).
- [ ] **1.2 VWAP Execution Strategy (`VwapStrategy`)**
  - [ ] Port `StockSharp.Algo.Strategies.VwapStrategy` to Python.
  - [ ] Dynamic slice sizing proportional to historical exchange intraday volume curve (NSE 09:15–15:30 profile).
  - [ ] Real-time pace adjustment based on accumulated volume.
- [ ] **1.3 Percentage of Volume (POV) Slicer (`PovStrategy`)**
  - [ ] Port POV execution algorithm participating at target rate (e.g. 5% or 10% of market volume).
  - [ ] Dynamically speeds up during volume spikes and pauses during liquidity droughts.
- [ ] **1.4 Synthetic Iceberg Slicer (`IcebergStrategy`)**
  - [ ] Display small visible quantity while holding hidden balance in local order manager.
  - [ ] Automatically replenishes visible leg upon complete fill with randomized display size.

---

### Phase 2: Arbitrage & Relative Value Strategies (StockSharp Port) (M1) — Week 3–4
> Porting StockSharp arbitrage engines to capture risk-neutral spreads across Indian markets.

- [ ] **2.1 Statistical Arbitrage & Pairs Trading (`PairsTradingStrategy`)**
  - [ ] Port `StockSharp.Algo.Strategies.Arbitrage.PairsTradingStrategy`.
  - [ ] Johansen & Engle-Granger cointegration test module for asset pair selection.
  - [ ] Real-time spread calculation: $S_t = \ln(P_{A, t}) - \beta \ln(P_{B, t}) - \alpha$.
  - [ ] Dynamic Z-score threshold entry ($Z \ge 2.0$) with stop-loss at $Z \ge 3.5$ and mean exit at $Z = 0.0$.
  - [ ] Simultaneous two-leg order execution with leg-risk mitigation.
- [ ] **2.2 Cash-and-Carry Basis Arbitrage (`CashAndCarryStrategy`)**
  - [ ] Ingest spot equity (NSE) and near-month equity futures (NFO).
  - [ ] Detect mispriced basis exceeding financing cost + statutory taxes (STT, GST, Stamp Duty).
  - [ ] Long delivery equity (`CNC`), short near-month future; hold until expiry settlement at parity.
- [ ] **2.3 Index & ETF Basket Arbitrage (`BasketArbitrageStrategy`)**
  - [ ] Monitor price discrepancy between NIFTY 50 ETF (e.g. NIFTYBEES) and synthetic basket of underlying 50 scrips.
  - [ ] Execute synchronized basket creation/redemption arbitrage.

---

### Phase 3: Market Making & Quoting Strategies (StockSharp Port) (M2) — Week 5–6
> Porting StockSharp quoting and market-making strategies for high-frequency liquidity provision.

- [ ] **3.1 Passive Spread Quoting (`SpreadQuotingStrategy`)**
  - [ ] Port `StockSharp.Algo.Strategies.Quoting.QuotingStrategy`.
  - [ ] Place continuous bid at Best Bid and ask at Best Ask; automatically cancel-replace on market depth shifts.
  - [ ] Guard against adverse selection using Order Book Imbalance indicator from `honba-me`.
- [ ] **3.2 Avellaneda-Stoikov Market Maker (`AvellanedaStoikovStrategy`)**
  - [ ] Dynamic reservation price calculation based on inventory risk aversion parameter $\gamma$:
    $$R(s, q, t) = s - q \gamma \sigma^2 (T - t)$$
  - [ ] Asymmetric quoting skew: lowers bid and widens ask when inventory is long; raises bid when short.
- [ ] **3.3 Ladder Quoting (`LadderQuotingStrategy`)**
  - [ ] Multi-level grid quoting across 5 levels of market depth with position size decay.

---

### Phase 4: Trend Following & Breakout Strategies (StockSharp Port) (M3) — Week 7–8
> Porting StockSharp classic and adaptive trend followers.

- [ ] **4.1 Turtle Trading System (`TurtleStrategy`)**
  - [ ] Port classical Richard Dennis 20-day (System 1) and 55-day (System 2) Donchian breakouts.
  - [ ] Volatility-normalized position sizing based on 20-day ATR ($N$).
  - [ ] Pyramiding logic: add 1 unit every $0.5N$ profit up to 4 units; hard stop at $2N$ from last entry.
- [ ] **4.2 Adaptive Moving Average Crossover (`KamaCrossoverStrategy`)**
  - [ ] Dual KAMA (Kaufman Adaptive Moving Average) strategy adapting to market noise ratio.
  - [ ] Suppresses whipsaw signals during sideways consolidation.
- [ ] **4.3 Multi-Timeframe Supertrend (`MultiSupertrendStrategy`)**
  - [ ] Higher-timeframe (1-hour) trend filter combined with lower-timeframe (5-minute) ATR trailing entry.

---

### Phase 5: Mean Reversion Strategies (StockSharp Port) (M4) — Week 9–10
> Porting StockSharp statistical and volatility-envelope mean reversion.

- [ ] **5.1 Bollinger Band + RSI Exhaustion (`BollingerRsiMeanReversion`)**
  - [ ] Long entry when price closes below Lower Bollinger Band ($2\sigma$) and RSI $< 25$.
  - [ ] Exit on reversion to Middle Band (20 SMA) or opposite band touch.
- [ ] **5.2 VWAP Reversion (`VwapBandReversion`)**
  - [ ] Trades intraday mean reversion when price deviates $\ge 2.5\sigma$ from session VWAP.
  - [ ] Strict 15:20 IST intraday square-off enforcement.
- [ ] **5.3 Ornstein-Uhlenbeck Mean Reversion (`OuMeanReversionStrategy`)**
  - [ ] Fits continuous-time Ornstein-Uhlenbeck stochastic process $dX_t = \theta (\mu - X_t) dt + \sigma dW_t$.
  - [ ] Computes half-life of mean reversion and trades only scrips with half-life $< 5$ trading days.

---

### Phase 6: Portfolio Allocation & Dynamic Rebalancing (StockSharp Port) (M5) — Week 11–12
> Porting StockSharp portfolio management and asset allocation models.

- [ ] **6.1 Equal Weight & Periodic Rebalancer (`EqualWeightRebalancer`)**
  - [ ] Maintains target weight allocations across universe with drift threshold bands (e.g. $\pm 5\%$).
- [ ] **6.2 Risk Parity Allocation (`RiskParityStrategy`)**
  - [ ] Weights assets inversely proportional to their 60-day historical volatility so each asset contributes equal risk.
- [ ] **6.3 Mean-Variance Markowitz Rebalancer (`MarkowitzStrategy`)**
  - [ ] Solves quadratic optimization maximizing Sharpe ratio subject to minimum weight and sector concentration constraints.

---

## 3. Verification & CI Test Suite

- [ ] `pytest tests/`: 100% test pass rate across all ported strategies.
- [ ] Golden vector tests comparing trade signals of ported strategies against StockSharp C# reference implementations.
- [ ] Stress-testing each strategy in `honba-ya-backtest` across 5-year historical datasets with exact Indian tax models.
