# `honba-strategies` Agent Guidelines & Architecture Invariants

**Subsystem**: Strategies (Production Strategy Catalog)
**Language**: Python
**Primary Responsibility**: Ported StockSharp strategies, algorithmic execution models, and quantitative alphas.

---

## 1. Role & Architectural Hints
* `honba-strategies` is the canonical strategy repository:
  1. **Python-First Strategy SDK**: Inherits from `honba.Strategy`.
  2. **Ported StockSharp Strategies**: Quoting, Arbitrage, Market Making, TWAP/VWAP slicers, Turtle breakout, and Risk Parity.
  3. **Declarative Parameters**: All tunable inputs must use `Parameter(default=..., min=..., max=..., step=...)`.
  4. **Strict Research-Live Parity**: The exact same strategy class executes against historical Parquet bars and live WebSocket feeds.
* **Idea Inheritance**:
  - **Jesse**: Clean strategy lifecycle hooks (`on_start`, `on_bar`, `on_tick`, `on_order_event`, `on_stop`).
  - **StockSharp**: Quantitative order execution styles and hedging logic.

---

## 2. Coding Guidelines (DDD & TDD)
* **Zero Floats Policy**: Use `decimal.Decimal` for prices, stop levels, and quantities.
* **TDD & Parallel Test Directory Rule (MANDATORY)**:
  - Tests live in `tests/` parallel to `src/` (e.g. `tests/unit/`, `tests/integration/`).
  - Red-Green-Refactor cycle on every strategy implementation.

---

## 3. Development & CI Workflow
* **Linting & Formatting**:
  ```bash
  ruff check .
  ruff format --check .
  ```
* **Testing**:
  ```bash
  pytest -q
  ```
