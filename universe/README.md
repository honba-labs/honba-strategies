# Universe

> **Migration in progress.** The equal-weight Alpha 30 rebalancer moved to
> [`portfolio/rebalancing/equal_weight`](../portfolio/rebalancing/equal_weight/README.md)
> (a thin `PortfolioStrategy` configured by `universe = "nifty200_alpha30"`). The remaining
> strategies under `universe/alpha/` (`factor`, `low_vol`, `mean_reversion`, `momentum`,
> `quality`) carry selection logic and are pending migration to Selector-based portfolio
> strategies under `portfolio/`. Until then they keep using `universe/alpha/base.py`.



## Understanding the "Alpha" Metric
Unlike simple raw price returns, this strategy uses **Jensen's Alpha**, which is derived from the Capital Asset Pricing Model (CAPM). It isolates a stock's idiosyncratic structural outperformance over what would be expected based on its systemic market risk ($\beta$):

$$\text{Jensen's Alpha } (\alpha) = R_i - [R_f + \beta_i \cdot (R_m - R_f)]$$

Where:
* $R_i$ = Trailing 1-year return of the stock
* $R_f$ = Risk-free rate of return
* $\beta_i$ = Beta coefficient of the stock (systemic sensitivity to the parent index)
* $R_m$ = Return of the benchmark index (Nifty 200)

---

## Factor Differentiation: Alpha vs. Momentum vs. Quality vs. Low Volatility

Smart-Beta/Factor investing abandons pure market-capitalization weighting. Instead, it weights stocks based on specific financial anomalies or behavioral metrics. The table below details how these individual factor pillars function:

| Factor Strategy | Primary Objective | Mathematical Basis / Metric | Rebalancing | Risk/Return Profile |
| :--- | :--- | :--- | :--- | :--- |
| **Alpha** <br>*(e.g., Nifty200 Alpha 30)* | Captures structural **risk-adjusted outperformance** relative to a specific benchmark market index. | **Jensen's Alpha:** Calculated using 1-year trailing prices against CAPM predictions. | **Quarterly** <br>*(Captures rapid trend-shifts)* | **Very High Risk / High Reward:** Highly cyclical; subject to aggressive sector rotation and drawdowns during market reversals. |
| **Momentum** <br>*(e.g., Nifty200 Momentum 30)* | Capitalizes on the persistence of existing **price trends** (buying high to sell higher). | **Normalized Momentum Score:** Combines 6-month and 12-month total price returns, divided by daily return volatility. | **Semi-Annually** <br>*(Prevents high transaction churn)* | **High Risk / High Momentum:** Tends to excel in sustained bull runs but faces systemic "momentum crashes" when secular trends suddenly pivot. |
| **Quality** <br>*(e.g., Nifty200 Quality 30)* | Identifies financially sound, structurally **durable businesses** with resilient fundamentals. | **Composite Quality Score:** Evenly weights high **Return on Equity (ROE)**, low **Financial Leverage (Debt/Equity)**, and low **EPS Growth Variability**. | **Semi-Annually** | **Moderate Risk / Steady Returns:** Defensive footprint; typically outperforms during sideways or bearish market environments. |
| **Low Volatility** <br>*(e.g., Nifty100 Low Volatility 30)*| Protects capital by choosing stocks with the most **stable, predictable price paths**. | **Standard Deviation:** Ranks stocks by the lowest standard deviation of daily price returns over a trailing 1-year period. | **Semi-Annually** | **Lower Risk / Stable Returns:** Dampens portfolio drawdowns during market panics; lags during aggressive, liquidity-driven rallies. |



## What is Alpha 30?

This section contains strategies that trade stocks from the **Nifty200 Alpha 30** list.

**What does that mean?**
The Nifty200 Alpha 30 is a special list of 30 stocks picked from the top 200 Indian companies (the Nifty 200). These 30 stocks are chosen because they have a strong track record of beating the market (a measure known as "Alpha"). 

The list is updated every three months to make sure it always has the best-performing stocks. Because these are large, actively traded companies, it is very easy to buy and sell them quickly.

The strategies in this folder all follow a similar pattern:
- **Trade a group of stocks:** Instead of putting all your money into one company, they spread your capital across all the stocks in the Alpha 30 list.
- **Regular updates (Rebalancing):** Over time, some stocks go up and some go down. These strategies regularly adjust the portfolio (like every 15 days) to make sure your money stays properly balanced. They also automatically buy new stocks when they join the Alpha 30 list and sell ones that are removed.

## Inside a Strategy Folder

If you open any strategy folder here, you will find these standard files:

- `strategy.py` — The actual Python code that runs the trading logic.
- `config.toml` — Settings you can easily change (like starting capital or how often to rebalance).
- `README.md` — Simple instructions and notes for that specific strategy.
- `tests/` — Automated checks to make sure the code is working correctly.
- `backtest_result.json` — reference back-test summary

## Common design patterns

- **Universe source** — prefer the engine’s live universe (`ctx.universe("NIFTY200_ALPHA_30")`). A static seed list in `config.toml` is only a fallback for offline tests.
- **Equal-weight or score-weight** — most strategies either equal-weight the current members or weight by a factor score, then rebalance periodically.
- **Membership changes** — on every rebalance, names that left the index are fully exited; names that entered are sized to target.
- **Rebalance cadence** — typically 15 trading days or quarterly (aligned with the official index review). Override via `rebalance_days` in `config.toml`.
- **Sizing** — use `honba.strategies.sizing.whole_shares` so lot-size constraints are respected; leave a small cash buffer (`allocation < 1.0`).

## Tags

Strategies in this folder commonly carry the tags:

- `alpha`
- `universe`
- `breadth` / `statistical` (when ranking is used)
- `momentum`, `volatility`, or `trend` depending on the factor

## Running

```bash
# from the honba-strategies root (honba must be importable)
pytest alpha_universe/