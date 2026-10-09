# Universe

> **Migration complete.** The strategies under `universe/alpha/` (`factor`, `low_vol`,
> `mean_reversion`, `momentum`, `quality`) are now Selector-based `PortfolioStrategy` implementations
> configured over the `nifty200_alpha30` universe.



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
