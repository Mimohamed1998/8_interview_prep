# Feature Engineering EDA Summary — Demand Intelligence Pipeline

**Notebook:** `pipelines/5_feature_engineering/feature_engineering_eda.ipynb`  
**Depends on:** `docs/11_feature_merging_guide.md`  
**Outputs:** `data/Intermediate/*_reduced.parquet`

---

## What This Step Does

Before training the XGBoost models the feature matrix is reduced in two ways:

1. **Row-level activity filter** — removes dormant outlet-item time-points that carry no signal
2. **Correlation filter** — removes features that are redundant with a retained partner (|r| ≥ 0.80)

Both filters are applied consistently across all 9 model variants so the training matrix is identical in structure for each cluster.

---

## Step 1 — Row-Level Activity Filter

### Logic

At every row `(outlet_id, item_code, year_month = T)` check whether the outlet-item had **any demand in the 6 months before T**.  The column `demand_event_rate_6m` (from `zero_inflation_features.parquet`) already captures this: it is the fraction of months in `[T−6, T−1]` where `net_quantity > 0`.

```
KEEP row  ←→  demand_event_rate_6m > 0
DROP row  ←→  demand_event_rate_6m == 0  (zero sales for the entire prior 6-month window)
```

**Example:** a row at `2018-01` is kept only if there was at least one non-zero sale between `2017-07` and `2017-12`.

### Result

| | Rows |
|---|---|
| Before filter | 100,618,320 |
| After filter | 23,442,722 |
| **Removed** | **77,175,598 (76.7%)** |

The large reduction reflects how sparse the raw outlet-item-month panel is — most rows are zero-demand history for inactive combinations.

---

## Step 2 — Correlation Analysis

### Sample Strategy

A memory-safe sample of **800 random outlet IDs** (~280,000 rows) was collected from the filtered matrix. Pearson correlations were computed on all 64 numeric feature columns after excluding:
- Identifiers (`outlet_id`, `item_code`, `year_month`)
- Categorical strings (`territory_id`, `region`, `district`, `province`, `product_category`, `product_line`, `brand`, `cluster_definition`, `demand_class`)
- Target labels (`target_qty_raw`, `target_qty_log1p`, `target_is_nonzero`, `target_log1p_net_sales`)

### High-Correlation Pairs Found (|r| ≥ 0.80)

29 pairs were identified. The top offenders by correlation magnitude:

| Feature A | Feature B | \|r\| | Reason for redundancy |
|---|---|---|---|
| `months_since_last_purchase` | `consecutive_zeros` | 0.997 | Same signal, different representations |
| `year` | `months_elapsed` | 0.977 | Both encode calendar time monotonically |
| `net_quantity` | `gross_quantity` | 0.970 | Returns are a small fraction of gross |
| `roll_nonzero_count_6m` | `demand_event_rate_6m` | 0.962 | Rate = count / 6 |
| `lag_qty_12m` | `lag_sales_12m` | 0.955 | Lag qty × stable price ≈ lag sales |
| `net_sales` | `gross_sales` | 0.954 | Returns are a small fraction |
| `lag_qty_6m` | `lag_sales_6m` | 0.953 | Same relationship at 6m |
| `roll_mean_qty_6m` | `roll_std_qty_6m` | 0.945 | High-volume SKUs have high variance |
| `lag_qty_1/2/3m` | `lag_sales_1/2/3m` | 0.940 | Consistent across all short lags |
| `roll_mean_qty_3m` | `roll_std_qty_3m` | 0.935 | Same mean-variance relationship at 3m |
| `roll_nonzero_count_12m` | `demand_event_rate_12m` | 0.919 | Rate = count / 12 |

---

## Step 3 — Greedy Feature Reduction

### Algorithm

Repeatedly drop the feature that participates in the most threshold violations.  Ties broken by highest total correlation burden.  Repeats until no remaining pair exceeds 0.80.

### Outcome

| | Feature columns |
|---|---|
| Before | 77 |
| After | **54** |
| Dropped | **23** |

Max |r| in the retained set: **0.766** (safely below 0.80).

### Dropped Features by Source Table

**`base_features_for_modeling` — 20 dropped**

| Dropped column | Retained partner | \|r\| |
|---|---|---|
| `net_quantity` | `yoy_growth` | 0.845 |
| `gross_quantity` | `net_quantity` | 0.970 |
| `gross_sales` | `net_sales` | 0.954 |
| `months_elapsed` | `year` | 0.977 |
| `lag_qty_1m` | `lag_sales_1m` | 0.940 |
| `lag_qty_2m` | `lag_sales_2m` | 0.940 |
| `lag_qty_3m` | `lag_sales_3m` | 0.940 |
| `lag_qty_6m` | `lag_sales_6m` | 0.953 |
| `lag_qty_12m` | `lag_sales_12m` | 0.955 |
| `roll_mean_qty_6m` | `roll_mean_qty_12m` / `roll_std_qty_6m` | 0.888–0.945 |
| `roll_mean_qty_12m` | `roll_std_qty_12m` | 0.928 |
| `roll_std_qty_3m` | `roll_mean_qty_3m` | 0.935 |
| `roll_std_qty_6m` | `roll_std_qty_12m` | 0.912 |
| `roll_mean_sales_6m` | `roll_mean_sales_12m` | 0.877 |
| `roll_std_sales_6m` | `roll_mean_sales_12m` | 0.823 |
| `roll_nonzero_count_3m` | `months_since_last_purchase` | 0.825 |
| `roll_nonzero_count_6m` | `demand_event_rate_6m` | 0.962 |
| `roll_cv_qty_6m` | `roll_cv_qty_12m` | 0.925 |
| `momentum_ratio` | `short_long_ratio` | 0.898 |
| `current_return_rate` | `n_returns` | 0.876 |

**`zero_inflation_features` — 2 dropped**

| Dropped | Retained partner | \|r\| |
|---|---|---|
| `consecutive_zeros` | `months_since_last_purchase` | 0.997 |
| `demand_event_rate_12m` | `roll_nonzero_count_12m` | 0.919 |

**`enriched_sku_lookup` — 1 dropped**

| Dropped | Retained partner | \|r\| |
|---|---|---|
| `sku_cv` | `demand_class_encoded` | 0.859 |

**`seasonal_index_lookup`, `target_features` — 0 dropped**

---

## Retained Features (54 total)

### Time / Calendar (4)
`year`, `month_int`, `sin_1`, `cos_1`, `sin_2`, `cos_2`, `sin_3`, `cos_3`

### Demand Level (3)
`net_sales`, `yoy_growth`, `price_per_unit`

### Lag Features — Sales (5)
`lag_sales_1m`, `lag_sales_2m`, `lag_sales_3m`, `lag_sales_6m`, `lag_sales_12m`

### Rolling Window — Quantity (5)
`roll_mean_qty_3m`, `roll_std_qty_12m`, `roll_cv_qty_3m`, `roll_cv_qty_12m`, `roll_nonzero_count_12m`

### Rolling Window — Sales (2)
`roll_mean_sales_3m`, `roll_mean_sales_12m`

### Return Features (4)
`return_quantity`, `return_sales`, `n_returns`, `roll_return_rate_3m`, `roll_return_rate_6m`

### Transaction Features (1)
`n_invoices`

### Trend / Momentum (3)
`trend_slope_approx`, `short_long_ratio`, `is_peak_month`, `is_trough_month`

### Zero-Inflation (2)
`demand_event_rate_6m`, `months_since_last_purchase`

### SKU Lookup (4)
`demand_class_encoded`, `sku_activity_rate`, `sku_log_total_qty`, `is_structural_collapse`, `is_hyper_growth`

### Seasonal (1)
`seasonal_index`

---

## Output Files

All written to `data/Intermediate/`:

| File | Rows | Cols | Size |
|---|---|---|---|
| `base_features_reduced.parquet` | 23,442,722 | 44 | 407.1 MB |
| `zero_inflation_features_reduced.parquet` | 23,442,722 | 5 | 19.3 MB |
| `target_features_reduced.parquet` | 23,442,722 | 7 | 36.6 MB |
| `enriched_sku_lookup_reduced.parquet` | 50 | 7 | < 1 MB |
| `seasonal_index_lookup_reduced.parquet` | 600 | 3 | < 1 MB |

A convenience file `full_reduced_modeling_matrix.parquet` is also saved with all five tables pre-joined (23,442,722 rows × 57 columns).

---

## How to Load for Modelling

Follow the same join pattern from `docs/11_feature_merging_guide.md` but point at the reduced files:

```python
import polars as pl
from pathlib import Path

INT_DIR = Path("data/Intermediate")

lf = (
    pl.scan_parquet(INT_DIR / "base_features_reduced.parquet")
    .join(pl.scan_parquet(INT_DIR / "zero_inflation_features_reduced.parquet"),
          on=["outlet_id", "item_code", "year_month"], how="left")
    .join(pl.scan_parquet(INT_DIR / "target_features_reduced.parquet"),
          on=["outlet_id", "item_code", "year_month"], how="left")
    .join(pl.scan_parquet(INT_DIR / "enriched_sku_lookup_reduced.parquet"),
          on="item_code", how="left")
    .join(pl.scan_parquet(INT_DIR / "seasonal_index_lookup_reduced.parquet"),
          on=["item_code", "month_int"], how="left")
)

# Filter to a model cell before collecting
cell_df = lf.filter(pl.col("cluster_definition") == "Power").collect()
```

---

## Key Decisions

| Decision | Rationale |
|---|---|
| Activity threshold: `demand_event_rate_6m > 0` | Removes rows with no signal in any of the 6 preceding months; avoids penalising seasonal gaps shorter than 6 months |
| Kept `lag_sales_*` over `lag_qty_*` | Sales captures both volume and price signal; qty is recovered via `price_per_unit` when needed |
| Kept `year` over `months_elapsed` | `year` is interpretable as a level effect; `months_elapsed` is a monotonic duplicate |
| Kept `demand_event_rate_6m` over `roll_nonzero_count_6m` | Normalised rate is scale-invariant across different window sizes |
| Kept `months_since_last_purchase` over `consecutive_zeros` | Directly interpretable dormancy measure; same information, less noisy encoding |
| Targets never dropped | `target_*` columns are labels, not input features — excluded from correlation analysis entirely |
