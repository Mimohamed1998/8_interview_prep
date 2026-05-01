# Feature Engineering Catalog — Demand Forecasting Pipeline

> **Scope:** Feature set for the XGBoost demand forecasting grid (Power / High-Value Active / Low-Value Sporadic) × (Continuous / Intermittent / Lumpy).  
> **Primary source table:** `outlet_sku_monthly_demand.parquet` — grain: (outlet_id, item_code, year_month)  
> **Training window:** Jan 2015 – Dec 2019 (60 months, 5 full seasonal cycles)  
> **Target:** net_quantity at t+2 (2-month-ahead forecast horizon)  
> **Prepared:** 2026-05-01

---

## Overview

The feature matrix enriches the fact table with six layers of information:

| Layer | Source | Join Key |
|---|---|---|
| Item demand class | `item_classification.parquet` | item_code |
| Outlet cluster tier | `outlet_cluster_definitions.parquet` | outlet_id |
| Outlet behavioural profile | `outlet_features.parquet` | outlet_id |
| SKU national statistics | `m3_sku_demand_continuity.parquet` | item_code |
| Territory context | `monthly_territory_demand.parquet` | (territory_id, year_month) |
| Time-series features | Computed from the fact table itself | — |

Churned outlets are **excluded** from the feature matrix. The Churned segment requires a separate reactivation scoring model.

---

## 1. Target Variables (4)

| Feature | Formula | Notes |
|---|---|---|
| `target_qty_raw` | `net_quantity` shifted forward by 2 months, per (outlet_id, item_code) | Raw future quantity — retain for back-transformation |
| `target_qty_log1p` | `log1p(target_qty_raw)` | **Primary regression target** for all XGBoost regressors |
| `target_is_nonzero` | `1 if target_qty_raw > 0 else 0` | **Stage-1 binary target** for the Lumpy two-stage classifier |
| `target_log1p_net_sales` | `log1p(net_sales)` shifted forward by 2 months | Optional revenue-denominated target |

**Notes:**
- The last 2 rows of every outlet-SKU series will have null targets — this is correct. Drop them during model training.
- For the Lumpy two-stage model: Stage 1 uses `target_is_nonzero`; Stage 2 uses `target_qty_log1p` conditioned on Stage 1 predicting a non-zero event.

---

## 2. Lag Features (10)

All lags are computed on `log1p(metric)` before shifting. This maintains a consistent scale with the log-transformed target.

**Partitioning:** `.shift(n).over([outlet_id, item_code])` — requires data sorted by (outlet_id, item_code, year_month).

| Feature | Shift (n) | Source Metric | Null Rate |
|---|---|---|---|
| `lag_qty_1m` | 1 | net_quantity | ~1.7% (first month per series) |
| `lag_qty_2m` | 2 | net_quantity | ~3.3% |
| `lag_qty_3m` | 3 | net_quantity | ~5.0% |
| `lag_qty_6m` | 6 | net_quantity | ~10.0% |
| `lag_qty_12m` | 12 | net_quantity | ~20.0% — **same month last year** |
| `lag_sales_1m` | 1 | net_sales | ~1.7% |
| `lag_sales_2m` | 2 | net_sales | ~3.3% |
| `lag_sales_3m` | 3 | net_sales | ~5.0% |
| `lag_sales_6m` | 6 | net_sales | ~10.0% |
| `lag_sales_12m` | 12 | net_sales | ~20.0% |

**Demand-class notes:**
- Continuous: lag_qty_12m is critical — captures the strong seasonal pattern (strength 0.936).
- Intermittent/Lumpy: lags will be zero-inflated; the zero value is meaningful signal, not missing data.

---

## 3. Rolling Statistics (19)

All rolling windows: 3m, 6m, 12m. All `.over([outlet_id, item_code])` on sorted data.

### Rolling means — quantity

| Feature | Window | Formula | Purpose |
|---|---|---|---|
| `roll_mean_qty_3m` | 3 | `net_quantity.rolling_mean(3, min_samples=1)` | Short-term demand level |
| `roll_mean_qty_6m` | 6 | `net_quantity.rolling_mean(6, min_samples=1)` | Medium-term demand level |
| `roll_mean_qty_12m` | 12 | `net_quantity.rolling_mean(12, min_samples=1)` | Full-year baseline |

### Rolling standard deviations — quantity

| Feature | Window | Formula | Purpose |
|---|---|---|---|
| `roll_std_qty_3m` | 3 | `net_quantity.rolling_std(3, min_samples=2)` | Short-term volatility |
| `roll_std_qty_6m` | 6 | `net_quantity.rolling_std(6, min_samples=2)` | Medium-term volatility |
| `roll_std_qty_12m` | 12 | `net_quantity.rolling_std(12, min_samples=2)` | Annual volatility |

### Rolling CVs — quantity (derived, second pass)

| Feature | Formula | Purpose |
|---|---|---|
| `roll_cv_qty_3m` | `roll_std_qty_3m / (roll_mean_qty_3m + 1e-8)` | Local intermittency measure — mimics per-window CV classification |
| `roll_cv_qty_6m` | `roll_std_qty_6m / (roll_mean_qty_6m + 1e-8)` | Medium-term erraticism |
| `roll_cv_qty_12m` | `roll_std_qty_12m / (roll_mean_qty_12m + 1e-8)` | Annual erraticism |

### Rolling means and std — sales

| Feature | Window | Formula |
|---|---|---|
| `roll_mean_sales_3m` | 3 | `net_sales.rolling_mean(3, min_samples=1)` |
| `roll_mean_sales_6m` | 6 | `net_sales.rolling_mean(6, min_samples=1)` |
| `roll_mean_sales_12m` | 12 | `net_sales.rolling_mean(12, min_samples=1)` |
| `roll_std_sales_6m` | 6 | `net_sales.rolling_std(6, min_samples=2)` |

### Rolling nonzero counts (intermittency indicators)

| Feature | Window | Formula | Purpose |
|---|---|---|---|
| `roll_nonzero_count_3m` | 3 | `(net_quantity > 0).rolling_sum(3, min_samples=1)` | Demand events in last 3 months; 0–3 |
| `roll_nonzero_count_6m` | 6 | `(net_quantity > 0).rolling_sum(6, min_samples=1)` | Demand events in last 6 months; 0–6 |
| `roll_nonzero_count_12m` | 12 | `(net_quantity > 0).rolling_sum(12, min_samples=1)` | Demand events in last 12 months; 0–12 |

---

## 4. Trend Features (4)

| Feature | Formula | Notes |
|---|---|---|
| `yoy_growth` | `(net_quantity − net_quantity.shift(12)) / (net_quantity.shift(12) + 1e-8)` | Year-on-year growth rate at outlet-SKU grain; null for first 12 months. Captures secular trend. |
| `momentum_ratio` | `roll_mean_qty_3m / (roll_mean_qty_6m + 1e-8)` | Recent 3-month demand vs medium 6-month demand. > 1 = accelerating, < 1 = decelerating. |
| `short_long_ratio` | `roll_mean_qty_3m / (roll_mean_qty_12m + 1e-8)` | Recent demand vs full-year baseline. Detects seasonal uplift and structural demand shifts. |
| `trend_slope_approx` | `(net_quantity.shift(1) − net_quantity.shift(6)) / 5.0` | Linear approximation of slope over last 6 months (units: quantity change per month). Uses raw values, not log1p. |

**Notes on structural trends:**
- SKUs in `prod_line3` have CAGR = −29.7%/yr. The `trend_slope_approx` will reflect this. Models for these SKUs should not extrapolate a single slope — use `is_structural_collapse` flag to trigger piecewise treatment.
- SKUs in `prod_line17` have CAGR = +163.6%. Use `is_hyper_growth` flag and `short_long_ratio` to capture adoption-curve dynamics.

---

## 5. Seasonal Features (12)

These are derived from `year_month` alone — no `.over()` partitioning needed.

| Feature | Formula | Notes |
|---|---|---|
| `month_int` | `int(year_month[5:7])` | 1–12 |
| `year` | `int(year_month[0:4])` | 2015–2019 |
| `months_elapsed` | `(year − 2015) × 12 + month_int` | Global linear time index: 1 = Jan 2015, 60 = Dec 2019. Encodes secular trend for XGBoost. |
| `sin_1` | `sin(2π × 1 × month_int / 12)` | Fourier k=1 — fundamental annual cycle |
| `cos_1` | `cos(2π × 1 × month_int / 12)` | Fourier k=1 |
| `sin_2` | `sin(2π × 2 × month_int / 12)` | Fourier k=2 — semi-annual component |
| `cos_2` | `cos(2π × 2 × month_int / 12)` | Fourier k=2 |
| `sin_3` | `sin(2π × 3 × month_int / 12)` | Fourier k=3 — quarterly component |
| `cos_3` | `cos(2π × 3 × month_int / 12)` | Fourier k=3 |
| `is_peak_month` | `1 if month_int == 10 else 0` | October = STL seasonal peak (strength 0.936) |
| `is_trough_month` | `1 if month_int == 4 else 0` | April = STL seasonal trough |
| `seasonal_index` | Pre-computed per (item_code, month_int): `mean_qty_month / mean_qty_all_months` from national training demand | Borrowed national-level index. Critical for the 97.4% of outlet-SKU pairs too sparse to estimate an outlet-specific seasonal pattern. Value > 1 = above-average month, < 1 = below-average. |

**Why both month dummies and Fourier?** `month_int` (1–12) allows XGBoost to learn arbitrary per-month effects. Fourier terms encode a smooth periodic pattern in a compact form (6 features instead of 11 dummies) — preferred for sparse outlet-SKU pairs.

---

## 6. Zero-Inflation Features (4)

Critical for Intermittent and Lumpy SKUs. These features directly mimic the inter-arrival component of Croston/SBA methods. Require a `.collect()` intermediate step (forward-fill is not composable in a single lazy pass).

| Feature | Formula | Notes |
|---|---|---|
| `months_since_last_purchase` | Row index − forward-filled index of last nonzero event, per (outlet_id, item_code) | Null if no prior event exists for this outlet-SKU. Large values signal dormant or churning behavior. |
| `consecutive_zeros` | Count of consecutive zero-demand months in the current zero-run (resets to 0 on a demand event) | 0 = demand event or first zero; 1 = one consecutive zero month, etc. Direct proxy for inter-arrival interval length. |
| `demand_event_rate_6m` | `(net_quantity > 0).rolling_mean(6, min_samples=1)` per (outlet_id, item_code) | Proportion of last 6 months with positive demand. Analogous to Croston's estimated p̂ (inter-arrival probability). Range 0–1. |
| `demand_event_rate_12m` | `(net_quantity > 0).rolling_mean(12, min_samples=1)` per (outlet_id, item_code) | Full-year demand event rate. Stable estimate of outlet-SKU activity probability. |

---

## 7. Return Rate Features (4)

Returns are non-random (chi-square p ≈ 0, linked to category) and trending upward (7.57% in 2015 → 11.38% in 2019). Model them explicitly rather than absorbing into the net demand signal.

| Feature | Formula | Source |
|---|---|---|
| `current_return_rate` | `return_quantity / (gross_quantity + return_quantity + 1e-8)` | Fact table — current month return fraction |
| `roll_return_rate_3m` | `sum(return_qty, 3m) / (sum(gross_qty + return_qty, 3m) + 1e-8)` | Fact table — 3-month smoothed return rate |
| `roll_return_rate_6m` | `sum(return_qty, 6m) / (sum(gross_qty + return_qty, 6m) + 1e-8)` | Fact table — 6-month smoothed return rate |
| `category_return_rate` | Static constant per product_category (from M2 analysis) | Constant join — Cat_2: 11.80%, Cat_3: 9.16%, Cat_4: 8.32%, Cat_5: 6.64%, Cat_6: 7.87%, Cat_7: 6.87% |

---

## 8. Outlet-Level Features (11)

Joined from `outlet_features.parquet` on `outlet_id`. These are static per outlet (computed over a trailing 12-month window — same value for every row of a given outlet).

| Feature | Source Column | Formula / Notes |
|---|---|---|
| `outlet_loyalty_ratio` | `loyalty_ratio` | active_months / 12 — how consistently the outlet buys |
| `outlet_avg_txn_per_active_month` | `avg_txn_per_active_month` | Transaction frequency per active month |
| `outlet_avg_net_sales_per_txn` | `avg_net_sales_per_txn` | Average basket value. Consider log1p at model training time (skewed). |
| `outlet_avg_qty_per_txn` | `avg_qty_per_txn` | Average basket size in units |
| `outlet_n_unique_skus` | `n_unique_skus` | SKU breadth — number of distinct SKUs purchased per month |
| `outlet_n_unique_categories` | `n_unique_categories` | Category breadth — 1 = focused, 7 = full portfolio |
| `outlet_return_rate` | `return_rate` | Outlet-level return propensity |
| `outlet_pct_cash_txn` | `pct_cash_txn` | Fraction of transactions paid in cash. Proxy for formality/credit risk. |
| `outlet_momentum` | `momentum` | (last 3 months net sales) / (first 9 months net sales) over trailing 12m — demand trajectory |
| `outlet_total_net_sales_log` | `log1p(total_net_sales)` | Outlet size. Log-transformed — raw skewness = 38.05. |
| `outlet_active_months` | `active_months` | Depth of activity: how many months in the trailing 12 had at least one invoice |

---

## 9. SKU-Level Features (6)

Joined from `m3_sku_demand_continuity.parquet` + `item_classification.parquet` on `item_code`. Static per SKU.

| Feature | Source / Formula | Notes |
|---|---|---|
| `demand_class` | `item_classification.parquet` — string | `Continuous`, `Intermittent`, or `Lumpy` — model cell column axis |
| `demand_class_encoded` | `{Continuous: 0, Intermittent: 1, Lumpy: 2}` | Int8 ordinal for tree-based features and grid_cell computation |
| `sku_activity_rate` | `activity_rate` from m3_sku_demand_continuity | National fraction of months with positive demand (0–1) |
| `sku_cv` | `cv` from m3_sku_demand_continuity | National CV of non-zero demand sizes. > 1.0 = Lumpy; 0.5–1.0 = Intermittent. |
| `is_structural_collapse` | `(product_line == 'prod_line3').cast(Int8)` | prod_line3: −29.7% CAGR; 31.2% of revenue. Do NOT extrapolate single linear trend. |
| `is_hyper_growth` | `(product_line == 'prod_line17').cast(Int8)` | prod_line17: +163.6% CAGR from near-zero base. Bass diffusion dynamics — full 5-year history underestimates current trajectory. |
| `sku_log_total_qty` | `log1p(total_quantity)` from m3_sku_demand_continuity | National-level SKU size over the full observation window |

---

## 10. Outlet Cluster Features (4)

Derived from the `cluster_definition` column (joined from `outlet_cluster_definitions.parquet`).

| Feature | Formula | Notes |
|---|---|---|
| `cluster_encoded` | `{Power: 0, High-Value Active: 1, Low-Value Sporadic: 2}` | Int8 ordinal — primary model row-axis selector |
| `is_power_outlet` | `(cluster_definition == 'Power').cast(Int8)` | 4,534 outlets = 72.22% of revenue — account-level model treatment |
| `is_high_value_active` | `(cluster_definition == 'High-Value Active').cast(Int8)` | K-Means cluster 0: ~4.1 txns/active month, ~$5,053 avg basket, 26% return rate |
| `is_low_value_sporadic` | `(cluster_definition == 'Low-Value Sporadic').cast(Int8)` | K-Means cluster 1: ~1.8 txns/active month, ~$1,264 avg basket, 5.5% return rate |

---

## 11. Territory Context Features (5)

Joined from `monthly_territory_demand.parquet` on `(territory_id, year_month)`. These provide the market-level signal that individual outlet demand is embedded within.

| Feature | Formula | Notes |
|---|---|---|
| `terr_net_quantity` | `net_quantity` (renamed) from territory table | Total territory demand for this month across all SKUs |
| `terr_net_sales` | `net_sales` (renamed) from territory table | Total territory revenue for this month |
| `terr_lag_qty_1m` | `terr_net_quantity.shift(1).over(territory_id)` | Territory demand last month — lagged market signal |
| `terr_roll_mean_qty_3m` | `terr_net_quantity.rolling_mean(3).over(territory_id)` | Territory demand momentum |
| `outlet_share_of_territory` | `net_quantity / (terr_net_quantity + 1e-8)` | Outlet's fractional share of territory demand. Proxy for relative market position. Note: territory demand here is all-SKU, so this is a rough share — can be refined to SKU-level territory aggregation if needed. |

**ANOVA note:** F = 50.32, p < 0.0001 confirms that territory-level means are NOT interchangeable. Territory context features capture this structural heterogeneity.

---

## 12. Interaction and Derived Features (3)

| Feature | Formula | Notes |
|---|---|---|
| `grid_cell` | `cluster_encoded × 3 + demand_class_encoded` | Integer 0–8 identifying the model cell in the 3×3 XGBoost grid. Use to partition data for per-cell model training. |
| `price_per_unit` | `net_sales / clip(net_quantity, lower=1)` | Implied unit price. Captures price changes, promotions, mix shifts. |
| `price_per_unit_roll_3m` | `roll_mean_sales_3m / (roll_mean_qty_3m + 1e-8)` | 3-month smoothed implied price. More stable than the single-month estimate. |

---

## Feature Summary Table

| Category | Count | Key purpose |
|---|---|---|
| Target variables | 4 | Regression + binary classification targets |
| Lag features | 10 | Autoregressive signal |
| Rolling statistics (mean/std/CV) | 13 | Demand level, variability, local CV |
| Rolling nonzero counts | 3 | Intermittency in recent window |
| Trend features | 4 | YoY growth, momentum, slope |
| Seasonal features | 12 | Month dummies, Fourier terms, seasonal index |
| Zero-inflation features | 4 | Inter-arrival dynamics (Croston analog) |
| Return rate features | 4 | Returns signal and category baseline |
| Outlet-level features | 11 | Behavioural profile (static per outlet) |
| SKU-level features | 6 | Demand class, national stats, structural flags |
| Cluster features | 4 | Outlet tier encoding |
| Territory context features | 5 | Market-level context |
| Interaction features | 3 | Grid cell, implied price |
| **Total** | **~83** | (+ 6 key/identifier columns) |

---

## Grid Cell to Model Mapping

The `grid_cell` feature encodes which XGBoost model handles each row:

| grid_cell | cluster_definition | demand_class | Model |
|---|---|---|---|
| 0 | Power | Continuous | XGBoost Regressor |
| 1 | Power | Intermittent | XGBoost Regressor |
| 2 | Power | Lumpy | XGBoost Regressor |
| 3 | High-Value Active | Continuous | XGBoost Regressor |
| 4 | High-Value Active | Intermittent | XGBoost Regressor |
| 5 | High-Value Active | Lumpy | **XGBoost Classifier + Regressor** (two-stage) |
| 6 | Low-Value Sporadic | Continuous | XGBoost Regressor |
| 7 | Low-Value Sporadic | Intermittent | XGBoost Regressor |
| 8 | Low-Value Sporadic | Lumpy | **XGBoost Classifier + Regressor** (two-stage) |

---

## Evaluation Metric by Demand Class

Do NOT use the same metric across all cells — RMSE/MAPE are invalid for zero-inflated series.

| Demand Class | Primary Metric | Secondary Metric | Notes |
|---|---|---|---|
| Continuous | RMSE (on log scale), MAPE | Coverage probability | Well-defined denominator |
| Intermittent | MASE | PIS (Periods in Stock) | MAPE breaks when actuals = 0 |
| Lumpy | MASE | PIS, service-level simulation | RMSE produces systematically biased CIs |
| All cells | **Revenue-weighted MAE** | — | Power outlets = 72% of revenue; unweighted metrics mask catastrophic failure on top accounts |

---

## Data Window

| Split | Period | Months | Purpose |
|---|---|---|---|
| Training | Jan 2015 – Dec 2019 | 60 | 5 full seasonal cycles — model fitting |
| Validation | 2019 H2 (rolling 12-month) | 12 | Hyperparameter tuning, early stopping |
| Hold-out test | Jan 2020 – Mar 2020 | 3 | COVID structural break test — expected degraded performance |

---

## Code Generation Prompt

Use this prompt to implement `pipelines/5_feature_engineering/feature_engineering.py`. Review and edit feature list above before using.

```
Implement pipelines/5_feature_engineering/feature_engineering.py.

## Project
/Users/mohamedinas/Desktop/SE_projects/8_stax_interview/8_interview_prep
Language: Python + Polars 1.40.1
Pattern reference: pipelines/4_item_product_classification/item_classification.py
  - sys.path.insert(0, str(Path(__file__).parent.parent.parent)) at top
  - from src.common.utils.config import load_config
  - public main(), private _build_*() helpers
  - logging.getLogger(__name__) with timing logs at each stage
  - if __name__ == "__main__": main()

## Inputs (all data/Intermediate/ unless noted)
- outlet_sku_monthly_demand.parquet: 123M rows; columns: outlet_id(str), item_code(str),
  year_month(str YYYY-MM), net_quantity(i64), net_sales(f64), gross_quantity(i64),
  gross_sales(f64), return_quantity(i64), return_sales(f64), n_invoices(u32), n_returns(u32),
  territory_id(str), region(str), district(str), province(str), product_category(str),
  product_line(str), brand(str)
- item_classification.parquet: item_code(str), demand_class(str: Continuous/Intermittent/Lumpy)
- outlet_cluster_definitions.parquet: outlet_id(str), cluster_definition(str:
  Power / High-Value Active / Low-Value Sporadic / Churned)
- outlet_features.parquet: outlet_id, loyalty_ratio, avg_txn_per_active_month,
  avg_net_sales_per_txn, avg_qty_per_txn, n_unique_skus, n_unique_categories, return_rate,
  recency_months, momentum, pct_cash_txn, total_net_sales, total_quantity, active_months, is_active
- monthly_territory_demand.parquet: territory_id, year_month, net_quantity, net_sales,
  gross_quantity, gross_sales, return_quantity, return_sales, n_unique_skus, region, district, province
- data/output/m3_sku_demand_continuity.parquet: item_code, product_category, product_line,
  brand, active_months, activity_rate, cv, demand_class, total_quantity

## Config additions needed in conf/conf.yml (add under item_classification:)
feature_engineering:
  training_window: {start: "2015-01", end: "2019-12"}
  target_horizon: 2
  rolling_windows: [3, 6, 12]
  category_return_rates:
    cat_2: 0.1180
    cat_3: 0.0916
    cat_4: 0.0832
    cat_5: 0.0664
    cat_6: 0.0787
    cat_7: 0.0687

## Output
data/Intermediate/feature_engineering.parquet — zstd compressed
Use lf.sink_parquet(out_path, compression="zstd") after all build steps.

## Function signatures

def _build_seasonal_index(demand_path, training_start, training_end) -> pl.DataFrame:
    # Compute per-(item_code, month_int) seasonal index from national training demand
    # seasonal_index = mean(net_quantity in month m) / mean(net_quantity all months), per SKU
    # Returns DataFrame[item_code: str, month_int: i32, seasonal_index: f64]

def _build_enriched_sku_features(sku_continuity_path, item_class_path) -> pl.DataFrame:
    # Join demand_class from item_classification onto m3_sku_demand_continuity
    # (drop demand_class from sku_continuity first if present, use item_classification as authoritative)
    # Add: demand_class_encoded ({Continuous:0, Intermittent:1, Lumpy:2}, Int8)
    #      is_structural_collapse = (product_line == 'prod_line3').cast(Int8)
    #      is_hyper_growth = (product_line == 'prod_line17').cast(Int8)
    #      sku_log_total_qty = log1p(total_quantity)
    #      sku_activity_rate = activity_rate (renamed)
    #      sku_cv = cv (renamed)
    # Returns DataFrame[item_code, demand_class(str), demand_class_encoded,
    #                   sku_activity_rate, sku_cv, is_structural_collapse,
    #                   is_hyper_growth, sku_log_total_qty]

def _build_territory_context(territory_path) -> pl.LazyFrame:
    # Select only [territory_id, year_month, net_quantity, net_sales] to avoid column conflicts
    # Rename net_quantity -> terr_net_quantity, net_sales -> terr_net_sales
    # Sort by [territory_id, year_month]
    # Add: terr_lag_qty_1m = terr_net_quantity.shift(1).over(territory_id)
    #      terr_roll_mean_qty_3m = terr_net_quantity.rolling_mean(3, min_samples=1).over(territory_id)
    # Returns LazyFrame[territory_id, year_month, terr_net_quantity, terr_net_sales,
    #                   terr_lag_qty_1m, terr_roll_mean_qty_3m]

def _build_base_lazy(demand_path, cluster_path, training_start, training_end) -> pl.LazyFrame:
    # pl.scan_parquet(demand_path) — NEVER pl.read_parquet for this file
    # filter year_month in [training_start, training_end]
    # left join cluster_definitions on outlet_id
    # filter cluster_definition in ['Power', 'High-Value Active', 'Low-Value Sporadic']
    # sort [outlet_id, item_code, year_month] — MUST be done once here before any .over() calls

def _build_time_features(lf) -> pl.LazyFrame:
    # Add year (Int32), month_int (Int32), months_elapsed
    # Add Fourier: sin_1/cos_1 (k=1), sin_2/cos_2 (k=2), sin_3/cos_3 (k=3)
    # Add is_peak_month (month_int==10), is_trough_month (month_int==4)
    # Use math.pi (not numpy) to keep expressions serializable

def _build_lag_rolling_features(lf) -> pl.LazyFrame:
    # Data is already sorted. All window expressions use .over([outlet_id, item_code]).
    # ONE with_columns([...]) call for all lags and rolling stats (single pass):
    #   Lags: lag_qty_{1,2,3,6,12}m = log1p(net_quantity).shift(n).over(...)
    #         lag_sales_{1,2,3,6,12}m = log1p(net_sales).shift(n).over(...)
    #   Rolling qty: roll_mean_qty_{3,6,12}m, roll_std_qty_{3,6,12}m
    #   Rolling sales: roll_mean_sales_{3,6,12}m, roll_std_sales_6m
    #   Rolling nonzero: roll_nonzero_count_{3,6,12}m = (net_quantity>0).cast(Int32).rolling_sum(w)
    #   Rolling return intermediates: _ret_sum_3m, _gross_ret_sum_3m, _ret_sum_6m, _gross_ret_sum_6m
    # SECOND with_columns for derived (need prior columns):
    #   roll_cv_qty_{3,6,12}m = roll_std / (roll_mean + 1e-8)
    #   yoy_growth = (net_quantity - net_quantity.shift(12).over(...)) / (shift12 + 1e-8)
    #   momentum_ratio = roll_mean_qty_3m / (roll_mean_qty_6m + 1e-8)
    #   short_long_ratio = roll_mean_qty_3m / (roll_mean_qty_12m + 1e-8)
    #   trend_slope_approx = (net_quantity.shift(1).over(...) - net_quantity.shift(6).over(...)) / 5.0
    #   current_return_rate = return_quantity / (gross_quantity + return_quantity + 1e-8)
    #   roll_return_rate_3m = _ret_sum_3m / (_gross_ret_sum_3m + 1e-8)
    #   roll_return_rate_6m = _ret_sum_6m / (_gross_ret_sum_6m + 1e-8)
    #   price_per_unit = net_sales / net_quantity.clip(lower_bound=1)
    # Drop temp _ret_sum_* columns

def _build_zero_inflation_features(lf) -> pl.LazyFrame:
    # MUST .collect() internally — forward_fill and cumsum not composable in single lazy pass
    # After collect, data is still sorted by [outlet_id, item_code, year_month]
    # Step 1: Add per-group sequential index:
    #   _grp_idx = pl.col("outlet_id").cum_count().over([outlet_id, item_code]) - 1  (0-based)
    #   _is_event = (net_quantity > 0).cast(Int32)
    # Step 2: Forward-fill last event index:
    #   _last_event_idx = when(_is_event==1).then(_grp_idx).otherwise(None)
    #                     .forward_fill().over([outlet_id, item_code])
    # Step 3: months_since_last_purchase = _grp_idx - _last_event_idx
    # Step 4: _event_cumsum = _is_event.cum_sum().over([outlet_id, item_code])
    # Step 5: _pos_in_run = pl.col("outlet_id").cum_count().over([outlet_id, item_code, _event_cumsum]) - 1
    # Step 6: consecutive_zeros = when(net_quantity==0).then(_pos_in_run).otherwise(0)
    # Step 7: demand_event_rate_6m = _is_event.cast(Float64).rolling_mean(6, min_samples=1).over([outlet_id, item_code])
    #         demand_event_rate_12m = same with window=12
    # Drop all temp columns (_grp_idx, _is_event, _last_event_idx, _event_cumsum, _pos_in_run)
    # Return df.lazy()

def _build_join_features(lf, outlet_df, sku_df, seasonal_df, terr_lf, cat_return_rates) -> pl.LazyFrame:
    # 1. Prepare outlet_df: select only needed columns, rename with outlet_ prefix,
    #    add outlet_total_net_sales_log = log1p(total_net_sales), drop total_net_sales
    #    Exclude from outlet_df: territory_id, region, province (already in fact table)
    # 2. lf.join(outlet_df.lazy(), on="outlet_id", how="left")
    # 3. lf.join(sku_df.lazy(), on="item_code", how="left")
    #    — this adds demand_class(str), demand_class_encoded, sku_activity_rate, sku_cv,
    #      is_structural_collapse, is_hyper_growth, sku_log_total_qty
    # 4. lf.join(seasonal_df.lazy(), on=["item_code", "month_int"], how="left")
    # 5. lf.join(terr_lf, on=["territory_id", "year_month"], how="left")
    #    add: outlet_share_of_territory = net_quantity / (terr_net_quantity + 1e-8)
    # 6. Add cluster encodings:
    #    cluster_encoded = cluster_definition.replace({Power:0, High-Value Active:1, Low-Value Sporadic:2}).cast(Int8)
    #    is_power_outlet, is_high_value_active, is_low_value_sporadic (Int8 flags)
    # 7. Add category_return_rate via pl.when/then/otherwise chain from cat_return_rates dict
    # 8. Add grid_cell = (cluster_encoded.cast(Int32) * 3 + demand_class_encoded.cast(Int32)).cast(Int8)
    # 9. Add price_per_unit_roll_3m = roll_mean_sales_3m / (roll_mean_qty_3m + 1e-8)

def _build_target(lf, horizon=2) -> pl.LazyFrame:
    # Add in one with_columns:
    #   target_qty_raw = net_quantity.shift(-horizon).over([outlet_id, item_code])
    # Then in second with_columns (needs target_qty_raw):
    #   target_qty_log1p = target_qty_raw.log1p()
    #   target_is_nonzero = (target_qty_raw > 0).cast(Int8)
    #   target_log1p_net_sales = net_sales.log1p().shift(-horizon).over([outlet_id, item_code])
    # DO NOT fill nulls in last 'horizon' rows — they are structurally absent and handled at training time

def main():
    # 1. load_config() — read feature_engineering section
    # 2. Build lookup tables: seasonal_df, sku_df, outlet_df, terr_lf
    # 3. _build_base_lazy() → lf
    # 4. _build_time_features(lf)
    # 5. _build_lag_rolling_features(lf)
    # 6. _build_zero_inflation_features(lf)  ← logs "Collected N rows for zero-inflation step"
    # 7. _build_join_features(...)
    # 8. _build_target(lf, horizon=target_horizon)
    # 9. Log: total columns, sample null % for 5 key features
    # 10. lf.sink_parquet(out_path, compression="zstd")

## Critical constraints
- NEVER use pl.read_parquet on outlet_sku_monthly_demand.parquet — always pl.scan_parquet
- Sort [outlet_id, item_code, year_month] happens ONCE in _build_base_lazy; never repeat
- _build_zero_inflation_features must .collect() → compute → .lazy(); log row count after collect
- shift(-horizon) for targets creates nulls at series end — do NOT fill them
- Use math.pi not numpy.pi in Fourier expressions
- Territory join: use _build_territory_context which selects only 4 cols — no region/district conflict
- In _build_enriched_sku_features: drop demand_class from sku_continuity before joining,
  use item_classification.parquet as the authoritative demand_class source
```

---

*Prepared: 2026-05-01. Feature definitions derived from EDA Modules M1–M5. All thresholds and constants sourced from documented EDA findings.*
