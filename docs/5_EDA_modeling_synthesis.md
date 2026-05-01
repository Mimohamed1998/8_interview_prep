# EDA Synthesis — Modeling Strategy & Technical Q&A

> **Scope:** Cross-notebook synthesis of M1–M5 EDA findings.  
> **Data:** 6,799,893 transactions · 50 SKUs · 26 product lines · 6 brands · 257 territories · 116,014 outlets · Jan 2015–Mar 2020 (63 months)  
> **Prepared:** 2026-05-01

---

## 0. Grounding Facts (What the EDA Established)

| Dimension | Key Number |
|---|---|
| Total gross sales | $14,210,136,851 |
| SKUs | 50 (across 7 categories, 26 product lines, 6 brands) |
| Analysis window | 63 consecutive months (zero gaps) |
| Overall return rate | 9.05–10.7% (varies by measurement basis) |
| National YoY growth (median) | +7.6% |
| Seasonal strength (STL) | **0.936 / 1.0** — maximum-class seasonality |
| Stationarity (national series) | I(1) — stationary after first differencing |
| Active outlets | 66,736 (42.6% of all 116,183 have churned) |
| Structural power outlets | 4,534 outlets = **72.22% of revenue** |
| Dominant brand (HHI) | **0.851** — effectively mono-brand |

---

## 1. Modeling Granularity: Brand / Category / Product Line / SKU — or Demand-Class?

### The short answer

**Model at SKU level, stratified by demand class.** Do not model at brand, category, or product line level as a primary structure. Use product line and category only as features or for reporting aggregation.

### Why each alternative fails

| Level | Why it is wrong here |
|---|---|
| **Brand** | HHI = 0.851. One brand dominates ~91.5% of revenue. Brand-level modeling collapses to a single model for almost all volume — no differentiation available. |
| **Product category** | 7 categories, but demand class is *not* aligned to category. Cat_1 has 5 Lumpy SKUs, 0 Continuous; Cat_4 has 3 Continuous, 6 Intermittent, 0 Lumpy. Same category → completely different model needs. Category is a reporting dimension, not a modeling boundary. |
| **Product line** | 26 product lines, CAGR from +163.6% (prod_line17) to -46.7% (prod_line20). However, product line maps to commercial strategy (Defend/Nurture/etc.), not to statistical demand behavior. A product line can contain both a Continuous and a Lumpy SKU. |
| **Raw SKU without stratification** | 50 SKUs is small enough to model individually, but applying ARIMA to a Lumpy SKU is statistically invalid — the model will produce meaningless confidence intervals and systematically biased point forecasts. |

### The right structure: Demand-class stratification at SKU level

The EDA produced a clean, statistically validated demand classification for all 50 SKUs:

| Demand Class | n SKUs | % Volume | Model Family |
|---|---|---|---|
| **Continuous** | 7 (14%) | 16.5% | ARIMA(p,1,q)(P,1,Q)₁₂ or ETS |
| **Intermittent** | 29 (58%) | **69.9%** | Croston / SBA |
| **Lumpy** | 14 (28%) | 13.5% | ADIDA or ensemble with manual override |

This is not a reporting taxonomy — it is a modeling protocol. Each class requires a fundamentally different estimation method, evaluation metric (MASE not RMSE for intermittent), and safety-stock formula.

### What to use product line for

Product line CAGR belongs as a **trend feature** inside the model: the structural -27.4% median annual decline means most SKUs have a downward trend component that the model must account for. Product line membership can also serve as a feature in ML-based approaches (embedding or dummy).

### What to use category for

Category is the correct level for **return-rate adjustment**. Chi-square confirmed returns are non-independent of category (p ≈ 0). Apply category-specific return rates when converting gross sales to net demand signal before feeding the model.

---

## 2. Outlet Classification: K-Means vs. Domain-Driven, and the 3×3 Grid Strategy

### The proposed grid

```
                 | Item Class 1 (Continuous) | Item Class 2 (Intermittent) | Item Class 3 (Lumpy)
-----------------+---------------------------+-----------------------------+---------------------
Outlet Class 1   | Model 1                   | Model 2                     | Model 3
Outlet Class 2   | Model 4                   | Model 5                     | Model 6
Outlet Class 3   | Model 7                   | Model 8                     | Model 9
```

**Verdict: The grid strategy is architecturally sound and should be implemented — with one critical modification.**

### Why the grid works

- The ANOVA result (F = 50.32, p < 0.0001) statistically confirms that regional/outlet means are *not* interchangeable. A single national model produces structurally wrong signals.
- The demand-class axis provides a well-validated 3-level item classification (from M2/M3).
- 9 models over 50 SKUs and 63 months is computationally feasible and operationally manageable.

### The critical modification: Pre-separate power outlets before clustering

M5 found that **4,534 outlets (6.79% of active base) account for 72.22% of revenue**. These are not on the same distribution as the other 62,202 outlets — they are structural extremes, removed from the clustering population precisely because K-means is distortion-sensitive to outliers of this magnitude.

Applying the same model to power outlets as to mainstream outlets will produce wrong forecasts for the group that drives nearly three-quarters of your revenue.

**Recommended structure (4-tier, not 3-tier, on the outlet axis):**

| Outlet Tier | Population | Revenue Share | Classification Method | Treatment |
|---|---|---|---|---|
| **Power** | 4,534 | 72.22% | Threshold-based (3× IQR rule from M5) | Account-level models or dedicated tier |
| **Cluster A** | ~1/3 of 62,202 | ~10–12% | K-means (8-feature scaled matrix from M5) | Cluster model |
| **Cluster B** | ~1/3 of 62,202 | ~8–10% | K-means | Cluster model |
| **Cluster C** | ~1/3 of 62,202 | ~6–8% | K-means | Cluster model |
| **Churned** | 49,447 | ~0% current | Separate reactivation model | Not in main grid |

This gives a **4-row × 3-column = 12-model grid**, with a 13th model for churned outlet reactivation scoring.

### K-means setup (from M5 outputs)

The feature matrix is ready: 62,202 outlets × 8 VIF-filtered, scaled features:

1. `avg_txn_per_active_month` — transaction frequency
2. `avg_net_sales_per_txn_log` — spend per order
3. `avg_qty_per_txn_log` — basket size
4. `n_unique_categories` — category breadth
5. `return_rate` — returns propensity
6. `recency_months` — **⚠ zero variance — must be re-engineered before clustering**
7. `momentum_winsor` — spend trajectory
8. `pct_cash_txn` — payment behavior

**Action required:** Drop `recency_months` from the current scaled matrix or replace with continuous days-since-last-invoice before running K-means. With zero variance this feature is dead weight in the distance metric.

### K-means vs. domain-driven: the recommendation

Use **K-means for mainstream outlets** (62,202). Domain-driven tiers (e.g., large/medium/small by volume) embed assumptions about which behavioral dimensions matter — but M5's VIF analysis shows 8 independent behavioral dimensions exist, and domain rules typically capture only 1–2. K-means on the full feature vector will produce more commercially distinct, actionable segments.

Use **domain rule for power outlets** (4,534): the 3× IQR boundary from M5 already defines them cleanly — no need to cluster a group that warrants individual account management.

---

## 3. Should Outlier Months Be Removed?

### What the EDA shows

**Monthly return anomalies (M2):** 4 months exceeded the 95th percentile return threshold (~22.2%). These are discrete events, not a distributional tail.

**2020 data (M1):** Return rate in Jan–Mar 2020 = **24.66%**, vs 11.38% for full-year 2019. This is a 117% spike. Coincides with COVID-19 onset.

**YoY growth volatility (M2):** Range is -67.3% to +50.5%. The extreme negative months are almost certainly 2020.

### Recommendation: Do not remove — **separate**

Removing months destroys the continuity of the time series and corrupts lag feature engineering. Instead:

**Option A (Recommended): Truncate the series at December 2019.**

Treat Jan–Mar 2020 as out-of-sample. Rationale:
- The 2020 return spike to 24.66% likely reflects COVID disruption, which is a structural break — not recoverable business-as-usual seasonality.
- The analysis window 2015-01 → 2019-12 gives exactly **60 months = 5 clean years**, which is the ideal window for a seasonal model with period 12 (5 full cycles).
- Including the 3-month COVID stub biases both trend and seasonality estimates downward.

**Option B: Include 2020 with a COVID dummy variable.**

If you want to leverage 2020 data to improve parameter estimates, add a binary indicator `is_covid` (1 from Jan 2020 onward). This separates the structural break from the seasonal pattern. This is the better choice if you anticipate COVID-like disruptions in the forecast horizon.

**Option C: Use robust STL decomposition.**

STL with `robust=True` (already done in M2) down-weights anomalous observations automatically. Use the STL trend component as the deseasonalised series and let the residuals absorb the 2020 spike.

### On the 4 return anomaly months

Do **not** remove these months from the demand series. Returns affect the *target variable* (net sales), not the existence of the month. The correct treatment is to flag these months as high-return events and include them in return-rate calibration. The months themselves remain in the training set.

---

## 4. Should the Target Variable (Monthly Sales, 2-Month Lag) Be Log-Transformed?

### Short answer: **Yes, but with specific conditions.**

### Evidence from the EDA

| Observation | Evidence |
|---|---|
| Extreme right skew at outlet level | `total_net_sales` skewness = 38.05 before transform |
| Skew resolved by log | Log transform → skewness -0.34 |
| National series skew | Outlet-aggregated national sales: moderate, but outlet-SKU pairs are highly right-skewed |
| Variance non-stationarity | The 12-month MA in M2 shows the *level* of variance grows with the trend — classic multiplicative structure |
| YoY growth is the natural framing | CAGR, percentage change, ratios — all multiplicative concepts |

### When to apply the log transform

| Modeling scenario | Transform? | Reason |
|---|---|---|
| National-level ARIMA (d=1) on aggregate demand | Optional — the I(1) differencing partially stabilises variance. Log helps if residuals are heteroscedastic. | Use `log(1+y)` before differencing |
| Outlet × SKU models (62,202 outlets × 50 SKUs) | **Yes, strongly** — skewness is 38x at this grain | Log transform is mandatory |
| Croston / SBA for Intermittent SKUs | **No** — Croston operates on demand intervals and sizes separately; log does not apply to the inter-arrival component | |
| ML-based models (gradient boosting, etc.) | **Yes** — reduces sensitivity to extreme values in the loss function | |
| The 2-month lag itself | Apply the same transform as the target — lag of log(y) is consistent | |

### The 2-month lag specifically

A 2-month lag as target means you are predicting y_{t+2} given information at t. This is a valid demand planning horizon (order-to-delivery lead time equivalent). The log transform should be applied to y_{t+2}, and the lag features constructed from log(y_{t}), log(y_{t-1}), etc. to maintain a consistent scale throughout the feature space.

**One caution:** For Continuous SKUs modeled with SARIMA, the conventional approach is to take the log *then* the first (and possibly seasonal) difference. The order matters: `Δ₁Δ₁₂ log(y)` is the standard specification for a seasonal ARIMA on log-demand. Do not difference first then log — this produces meaningless negative-value inputs.

---

## 5. How Should Seasonal Impact Be Incorporated?

### What the EDA established

- **Seasonal strength = 0.936** — this is near-maximum. Anything above 0.6 requires explicit seasonal modeling. At 0.936 you are in the category where ignoring seasonality will make forecasts actively wrong, not just suboptimal.
- **Period = 12 months**. October is peak, April is trough.
- **The pattern is consistent enough to measure** — 5 full seasonal cycles (2015–2019) are available.

### Approach by model class

#### For ARIMA (7 Continuous SKUs)

Use **SARIMA(p, 1, q)(P, 1, Q)₁₂**:
- `d=1`: confirmed by ADF/KPSS stationarity tests
- `D=1`: one seasonal difference (accounting for year-on-year structural trend)
- `m=12`: period confirmed by STL decomposition
- Start with SARIMA(1,1,1)(1,1,1)₁₂ and iterate via AIC

Alternatively, **ETS(A,A,A)** (additive error, additive trend, additive seasonal) if the seasonal amplitude appears stable rather than growing with the level.

#### For ML-based models (outlet × SKU grain)

Encode seasonality as explicit features — **do not assume ML captures it automatically**:
1. **Month-of-year dummies** (11 binary variables) — direct, interpretable
2. **Seasonal index from M2** — pre-computed month-level index (Oct peak, Apr trough) as a continuous feature
3. **Fourier terms** — `sin(2πkt/12)` and `cos(2πkt/12)` for k=1,2,3 — lower-dimensional than 12 dummies, preferred when data is sparse
4. **STL seasonal component** — extract the STL seasonal residual for each SKU (at national grain) and use it as a feature at outlet level

For **97.4% Lumpy outlet-SKU pairs**, the outlet-level data is too sparse to estimate SKU-specific seasonal patterns. The correct approach is to **borrow the national-level seasonal index** (from M2's STL decomposition) and apply it as an offset or feature.

#### For Croston / SBA (29 Intermittent SKUs)

Croston does not natively handle seasonality. Options:
1. **Pre-deseasonalise before Croston**: Divide the demand series by the monthly seasonal index (from M2). Fit Croston on the deseasonalised series. Re-apply the seasonal multiplier to the forecast.
2. **Temporal aggregation**: Aggregate to quarterly demand before applying Croston — this partially absorbs monthly seasonal noise at the cost of forecast frequency.

#### For ADIDA (14 Lumpy SKUs)

ADIDA (Aggregate-Disaggregate Intermittent Demand Approach) already handles temporal aggregation. Apply at an annual or bi-annual frequency, then disaggregate back using the seasonal index from M2.

---

## 6. Additional Technically Interesting Questions and Findings

### 6.1 The 2020 Data Is Likely Useless for Trend Estimation (but Useful for Return Modeling)

2020 has 24.66% return rate vs 11.38% in 2019 — a 117% spike in 3 months. The truncated March 2020 data means the 2020 annual trend is unmeasurable. **Recommendation:** Exclude 2020 from trend and CAGR calculations. However, keep the 2020 return anomaly observations when calibrating the return-rate distribution — they represent tail risk that the inventory buffer must accommodate.

### 6.2 The 42.6% Churn Rate Is a Structural Signal Requiring Its Own Model

49,447 of 116,183 outlets have churned. This is not noise — it is 42.6% of your known commercial universe. A survival model (Cox hazard or Kaplan-Meier) on outlet tenure would:
- Identify which behavioral features (from M5's 8-feature matrix) predict churn risk
- Allow pre-emptive intervention before loss, not after
- Feed directly into the reactivation targeting problem

This is distinct from demand forecasting but should be built in parallel because churn changes the outlet population the demand model must serve.

### 6.3 The Power Outlet Revenue Concentration Implies a Different Forecasting Accuracy Standard

4,534 outlets = 72.22% of revenue. A 5% MAPE on these outlets is worth ~4× more revenue than a 5% MAPE on all mainstream outlets combined. Your model evaluation metric should be **revenue-weighted MAPE** or **revenue-weighted MAE**, not unweighted. An average MAPE that looks acceptable on paper can be failing catastrophically on the 4,534 accounts that matter most.

### 6.4 The prod_line3 Concentration Is an Existential Risk

prod_line3 = **31.2% of total revenue**, CAGR = -29.7% annually. At this trajectory:
- Year 1 from 2020: revenue from this line ≈ $3.11B (from $4.44B in the last year)
- Year 2: ≈ $2.19B
- Year 3: ≈ $1.54B

The demand model must not assume a linear trend extension for this line — a -29.7% CAGR is a structural collapse, not a cyclical dip. The trend feature for prod_line3 SKUs needs a structural break test and potentially a piecewise linear trend. If the trend is decelerating (rate of decline slowing), that changes the forecast materially.

### 6.5 Region_6 Decline Warrants a Structural Break Feature

Three of the five worst-declining territories are in region_6 (-34.1%, -29.2%, -24.6%). Before attributing this to the general portfolio decline, test whether region_6 experienced a discrete structural break (e.g., a competitor entry, distribution disruption). A Chow test on the region_6 revenue series would confirm. If a break exists, include a `region_6_post_break` dummy in all models serving that geography.

### 6.6 The Target Variable Has Two Components That Should Be Modeled Separately

`monthly_sales` = `gross_sales` - `returns`. Returns are modeled poorly as a residual. The EDA shows returns are:
- Non-random (chi-square p ≈ 0, linked to category)
- Trending upward (7.57% in 2015 → 11.38% in 2019 → anomalous 24.66% in 2020)
- Heterogeneous by category (6.64% cat_5 vs 11.80% cat_2)

**Recommendation:** Model gross demand and return rate as *separate targets*, then derive net demand:
- `gross_demand_model`: SARIMA / Croston / ADIDA by demand class
- `return_rate_model`: Logistic regression or beta regression on category, month, year trend
- `net_demand = gross_demand_model × (1 - return_rate_model)`

This produces better net forecast accuracy and gives you an actionable lever on the return side independently.

### 6.7 CV Heterogeneity Means Safety Stock Cannot Be Pooled

90th percentile CV = 1.072. At a 95% service level (Z = 1.65) and 1-month lead time, safety stock is `SS = Z × σ = 1.65 × (CV × mean_demand)`. The ratio of safety stock between a high-CV (CV = 1.07) and low-CV (CV = 0.34) SKU at the same mean demand is **3.15×**. Using a pooled or average CV will simultaneously over-stock the 8% of SKUs with low CV and critically under-stock the 72% of SKUs with high CV. Compute SS per-SKU from individual CV values.

### 6.8 prod_line17 Is the Only Growth Story — and Needs a Different Modeling Approach

prod_line17 CAGR = +163.6% (from a near-zero base to 2.1% of revenue). This is not a mature demand pattern — it is an adoption curve. Classical time series models trained on 5-year history will extrapolate a declining share of the older periods and underestimate current trajectory. For this line specifically, **use a Bass diffusion model or a short-window (12-month trailing) model** rather than the full 5-year history used for stable lines.

---

## 7. Recommended Modeling Architecture Summary

```
ITEM AXIS (columns)
├── Continuous (7 SKUs, 16.5% vol) → SARIMA(p,1,q)(P,1,Q)₁₂ or ETS(A,A,A)
├── Intermittent (29 SKUs, 69.9% vol) → Croston/SBA on deseasonalised demand
└── Lumpy (14 SKUs, 13.5% vol) → ADIDA + manual threshold override

OUTLET AXIS (rows)
├── Power outlets (4,534 = 72.22% revenue) → Account-level models, revenue-weighted MAPE
├── Cluster A (K-means, ~21K outlets) → Cluster-level feature-aggregated model
├── Cluster B (K-means, ~21K outlets) → Cluster-level feature-aggregated model
└── Cluster C (K-means, ~21K outlets) → Cluster-level feature-aggregated model

SEASONAL TREATMENT
├── Continuous/SARIMA → (1,1,1)(1,1,1)₁₂
├── Intermittent → pre-deseasonalise with M2 seasonal index, re-apply post-forecast
└── ML/Gradient Boosting → Fourier terms + seasonal index as features

TARGET VARIABLE
├── Log-transform: Yes (outlet-SKU grain, ML models) — log1p(y)
├── Log-transform: Optional (national ARIMA) — if residuals are heteroscedastic
├── Log-transform: No (Croston/SBA) — operates on intervals and sizes natively
└── Lag: 2-month target, apply same transform as target, construct lags from log(y)

DATA WINDOW
├── Training: Jan 2015 – Dec 2019 (60 months, 5 clean cycles)
├── Validation: 2019 H2 (12-month rolling window recommended)
└── Hold-out test: Jan 2020 – Mar 2020 (3 months, treated as COVID-break test)

RETURN RATE
└── Model separately by category → apply as multiplier to gross demand forecast
    Cat_2: 11.80%, Cat_3: 9.16%, Cat_4: 8.32%, Cat_6: 7.87%, Cat_7: 6.87%, Cat_5: 6.64%

EVALUATION METRICS
├── Continuous SKUs: RMSE, MAPE (on log scale), coverage probability
├── Intermittent/Lumpy SKUs: MASE, PIS (Periods in Stock), service level simulation
└── All: Revenue-weighted MAE (not unweighted — power outlets are 72% of revenue)
```

---

## 8. Data Foundation Health Checks (M1)

All blocking checks passed. The dataset is GO for modeling:

| Check | Result |
|---|---|
| Product join integrity | 100.0% |
| Region join integrity | 100.0% |
| Missing months | 0 (of 63) |
| Return sign convention | 0 violations |
| Overall return rate | 10.7% (trending upward, 2015–2019) |

---

*Synthesis covers M1 (data integration), M2 (temporal/demand), M3 (product portfolio), M4 (geographic), M5 (outlet profiling). All figures from notebook cell outputs — no placeholders.*
