# Item Classification — Definitions & Modeling Protocol

> **Scope:** Defines the three demand classes assigned to all 50 SKUs by the item classification pipeline (`pipelines/4_item_product_classification/item_classification.py`).  
> **Output table:** `data/output/item_classification.parquet`  
> **Source:** EDA Module M3 (Product Portfolio Analysis), validated against 63 months of national SKU demand (Jan 2015 – Mar 2020).

---

## Classification Overview

| Demand Class | SKUs | % SKUs | % Volume | Grid Column |
|---|---|---|---|---|
| **Continuous** | 7 | 14% | 16.5% | Item Class 1 |
| **Intermittent** | 29 | 58% | 69.9% | Item Class 2 |
| **Lumpy** | 14 | 28% | 13.5% | Item Class 3 |

The demand class is the primary axis for model selection. It is **not** a reporting taxonomy — it is a modeling protocol. Applying the wrong estimator to a demand class (e.g., ARIMA on a Lumpy SKU) produces statistically invalid forecasts.

---

## Feature Definitions

### `activity_rate`

```
activity_rate = n_active_months / total_months_in_window
```

- `n_active_months` = number of months where `gross_quantity > 0` at national level
- `total_months_in_window` = 63 (Jan 2015 – Mar 2020, all available months)
- Range: (0, 1]

A SKU with `activity_rate = 1.0` shipped product in every month of the observation window. A SKU with `activity_rate = 0.14` shipped in roughly 1 in 7 months.

### `cv` (Coefficient of Variation)

```
cv = std(nonzero_demand) / mean(nonzero_demand)
```

Computed on non-zero demand months only. This isolates demand size variability from demand intermittency (already captured by `activity_rate`). A `cv` close to 0 means demand is stable when it occurs; a `cv > 1.0` means demand is highly erratic even in active months.

---

## Classification Rules

The three rules are applied in priority order:

```
1. IF activity_rate >= 0.80 AND cv < 0.50  →  Continuous
2. IF activity_rate <  0.20 OR  cv > 1.00  →  Lumpy
3. ELSE                                     →  Intermittent
```

These thresholds were validated empirically in M3 against 50 SKUs and reproduce the EDA-confirmed distribution (7/29/14).

---

## Class Definitions

### Class 1 — Continuous

**Decision rule:** `activity_rate >= 0.80` AND `cv < 0.50`

A SKU is Continuous when it generates demand in at least 80% of months (≥ 50 of 63 months) and its active-month demand is stable (CV < 0.50). These SKUs exhibit a coherent time series with a detectable trend and seasonal pattern.

**Characteristics:**
- Demand present in ≥ 80% of observation months
- Low demand size variability (CV < 0.50)
- National-level series is stationary after first differencing (ADF/KPSS confirmed)
- Seasonal strength 0.936 applies — October peak, April trough

**Model family:** `SARIMA(p,1,q)(P,1,Q)_12` or `ETS(A,A,A)`  
Starting specification: `SARIMA(1,1,1)(1,1,1)_12`; iterate via AIC.

**Seasonal treatment:** Seasonal order `(P,1,Q)_12`; `D=1` captures year-on-year structural trend. `d=1` confirmed by stationarity tests.

**Log transform:** Optional at national level (apply if residuals are heteroscedastic). Mandatory at outlet-SKU grain — `log1p(y)` before differencing.

**Evaluation metrics:** RMSE, MAPE on log scale, coverage probability.

**Data window:** Train on Jan 2015 – Dec 2019 (60 months, 5 full seasonal cycles).

---

### Class 2 — Intermittent

**Decision rule:** Not Continuous AND NOT Lumpy (i.e., the residual class)

A SKU is Intermittent when demand occurs in 20–80% of months, or when it occurs frequently but with moderate variance (CV 0.50–1.00). These SKUs have irregular inter-demand intervals that make standard time-series methods unreliable.

Covers both the classical "intermittent" pattern (sparse, stable sizes) and the "erratic" pattern (frequent, high-variance sizes) — both are best handled by Croston-family estimators.

**Characteristics:**
- Demand may be absent in a significant fraction of months
- Demand size when present may vary substantially (CV 0.50–1.00 typical)
- 29 of 50 SKUs (58%) fall here, but these SKUs represent 69.9% of total volume
- This class is the highest-leverage for forecast accuracy improvement

**Model family:** `Croston` or `SBA (Syntetos-Boylan Approximation)`  
SBA is preferred — it corrects the upward bias in Croston's demand-size estimate.

**Seasonal treatment:** Pre-deseasonalise the national demand series using the M2 STL seasonal index before fitting Croston/SBA. Re-apply the seasonal multiplier to the point forecast at disaggregation time.

**Log transform:** Not applicable — Croston operates on inter-arrival intervals and demand sizes separately. Log transform does not apply to the inter-arrival component.

**Evaluation metrics:** MASE (mean absolute scaled error), PIS (periods in stock), service-level simulation at target fill rate.

**Important:** Do not use RMSE or MAPE for Intermittent SKUs — these metrics break down when the denominator (actual demand) is zero in intermittent periods.

**Data window:** Train on Jan 2015 – Dec 2019 (60 months).

---

### Class 3 — Lumpy

**Decision rule:** `activity_rate < 0.20` OR `cv > 1.00`

A SKU is Lumpy when demand is either very sparse (active fewer than 1 in 5 months) or highly erratic when it does occur (CV > 1.00). The combination of infrequent and irregular demand makes the series structurally different from both Continuous and Intermittent patterns.

**Characteristics:**
- Demand present in < 20% of months, OR demand size highly variable (CV > 1.00)
- 14 of 50 SKUs (28%) — these SKUs represent 13.5% of volume
- Classical ARIMA/ETS and even Croston produce systematically biased point forecasts
- Confidence intervals from standard models are statistically invalid

**Model family:** `ADIDA (Aggregate-Disaggregate Intermittent Demand Approach)` with manual override  
ADIDA aggregates the time series to a frequency (annual or bi-annual) where demand is no longer intermittent, fits a standard model on the aggregated series, then disaggregates back to the monthly level.

**Seasonal treatment:** Apply ADIDA at annual or bi-annual aggregation frequency. Disaggregate to monthly using the M2 STL seasonal index as the distributional weight.

**Log transform:** Not applicable — ADIDA aggregates prior to estimation; the aggregated series is not sparse.

**Evaluation metrics:** MASE, PIS (Periods in Stock), service-level simulation. Same metrics as Intermittent — RMSE/MAPE are invalid.

**Manual override:** For Lumpy SKUs with sporadic large orders (e.g., bulk seasonal events), a statistical forecast should be augmented with a judgment-based upper bound from sales account managers. The statistical model sets the baseline; manual override handles known future events.

**Data window:** Train on Jan 2015 – Dec 2019 (60 months). For ADIDA, this gives 5 annual observations — sufficient for a robust aggregate-level model.

---

## Special Modeling Flags

Two SKU groups require non-standard treatment regardless of demand class, based on product-line-level structural findings from M3:

| Flag | Trigger | Reason | Recommended Treatment |
|---|---|---|---|
| `structural_collapse_trend` | `product_line = prod_line3` | CAGR = -29.7%/yr; 31.2% of total revenue. This is a structural collapse, not a cyclical dip. | Apply structural break test (Chow). Use piecewise linear trend — do not extrapolate a single linear slope. |
| `bass_diffusion_short_window` | `product_line = prod_line17` | CAGR = +163.6% from near-zero base. Adoption-curve dynamics. | Use Bass diffusion model or 12-month trailing window — do not use full 5-year history, which will underestimate current trajectory. |
| `standard` | All other SKUs | No structural anomaly detected | Standard model for demand class applies |

---

## Relationship to the 12-Model Forecasting Grid

Item class is the **column axis** of the forecasting grid defined in the EDA synthesis:

```
                     | Class 1: Continuous | Class 2: Intermittent | Class 3: Lumpy
---------------------+---------------------+-----------------------+----------------
Power outlets        | Model 1             | Model 2               | Model 3
Cluster A outlets    | Model 4             | Model 5               | Model 6
Cluster B outlets    | Model 7             | Model 8               | Model 9
Cluster C outlets    | Model 10            | Model 11              | Model 12
```

Each cell in the grid selects both the estimation method (from item class) and the outlet-level feature aggregation strategy (from outlet tier). The 13th model handles churned-outlet reactivation scoring — this is separate from the demand forecasting grid.

---

## Output Table Schema (`item_classification.parquet`)

| Column | Type | Description |
|---|---|---|
| `item_code` | str | SKU identifier |
| `product_category` | str | Product category (7 categories) |
| `product_line` | str | Product line (26 lines) |
| `brand` | str | Brand (6 brands) |
| `demand_class` | str | `Continuous`, `Intermittent`, or `Lumpy` |
| `model_family` | str | Recommended estimator family |
| `eval_metric` | str | Primary evaluation metric(s) |
| `seasonal_treatment` | str | Seasonal handling approach |
| `log_transform_policy` | str | Log transform applicability |
| `modeling_flag` | str | `standard`, `structural_collapse_trend`, or `bass_diffusion_short_window` |
| `activity_rate` | f64 | Proportion of months with positive demand |
| `cv` | f64 | CV of demand size (non-zero months only) |
| `cv2` | f64 | CV² |
| `n_active_months` | i64 | Count of months with gross_quantity > 0 |
| `total_months_in_window` | i64 | Total months in observation window (63) |
| `mean_nonzero_demand` | f64 | Mean gross_quantity in active months |
| `std_nonzero_demand` | f64 | Std dev gross_quantity in active months |
| `total_quantity` | i64 | Total gross_quantity over window |
| `total_gross_sales` | f64 | Total gross sales over window |
| `total_net_sales` | f64 | Total net sales over window |
| `total_return_quantity` | i64 | Total return quantity over window |

---

*Prepared: 2026-05-01. Figures from M3 EDA notebook cell outputs — no placeholders.*
