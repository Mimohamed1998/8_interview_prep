# EDA Plan: WonderCo. Demand Intelligence

**Business Objective:** Optimise production planning by building a demand forecasting system anchored in outlet behaviour, product portfolio dynamics, and geographic performance.

**Status:** Pipeline 1 (DQ) and Pipeline 2 (Raw Processing) complete. This plan covers Pipeline 3 (EDA).

---

## Data Inputs

| File | Rows | Columns | Key Fields |
|------|------|---------|-----------|
| `data/input/processed/sales.parquet` | 6,799,893 | 12 | document_date, outlet_id, territory_id, item_code, document_type, net_sales, quantity |
| `data/input/processed/product.parquet` | 50 | 4 | item_code, product_category, product_line, brand |
| `data/input/processed/region.parquet` | 257 | 4 | territory_id, region, district, province |

All inputs use standardised snake_case column names (output of `pipelines/2_raw_processing`). Return rows carry negative `quantity` and negative `net_sales` — this sign convention is applied in Pipeline 2; Module 0 does not re-handle it.

---

## Business Goals → Analysis Mapping

| Goal | Description | Modules |
|------|-------------|---------|
| 1 | Outlet behavioural clusters and sub-clusters | 5, 6 |
| 2 | Monthly demand forecasting at outlet × SKU × month grain, aggregated to territory and national | 2, 3 |
| 3 | Buffer mechanism (service level + demand variability) | 2 |
| 4 | Maximum outlet potential within each cluster | 5, 6, 7 |

---

## Module 0 — Analytical Dataset Preparation

**File:** `pipelines/3_eda/00_dataset_preparation.py`
**Output path:** `data/Intermediate/` (from `conf/conf.yml → data.intermediate_path`)
**Purpose:** Build all analysis-ready datasets before any EDA notebook runs. The core problem this solves is the **sparse record problem**: raw sales data only contains rows where a transaction occurred. If an outlet had no sales in March, there is no March row — but for time series analysis, feature engineering, and clustering, March must exist with a value of zero. Each dataset is built with a fully exhaustive primary key so that zeroes are explicit, not absent.

---

### Dataset 1 — `base_sales_enriched.parquet`

**Purpose:** Single enriched fact table combining all three source tables. The foundation for all ad-hoc queries across the EDA.

**Primary Key:** Composite `(document_number, item_code)` — unique per line item on an invoice.

**Construction:**
1. Load `sales.parquet`. Parse `document_date` to datetime and derive `year_month = document_date.dt.strftime('%Y-%m')` (type: `str`, format: `yyyy-mm`).
2. Left join → `product.parquet` on `item_code`. Add `product_category`, `product_line`, `brand`.
3. Left join → `region.parquet` on `territory_id`. Add `region`, `district`, `province`.

**Output schema (key columns):**

| Column | Type | Notes |
|--------|------|-------|
| document_number | str | Invoice identifier |
| document_date | date | Transaction date |
| year_month | str | Derived month string, e.g. `2022-03` |
| outlet_id | str | Outlet identifier |
| territory_id | str | Territory identifier |
| item_code | str | SKU identifier |
| route_id | str | Route identifier |
| payment_term | str | Cash / credit |
| document_type | str | invoice / return |
| net_sales | float | Signed — negative for returns |
| quantity | int | Signed — negative for returns |
| product_category | str | From product dimension |
| product_line | str | From product dimension |
| brand | str | From product dimension |
| region | str | From region dimension |
| district | str | From region dimension |
| province | str | From region dimension |

**Estimated rows:** ~6.8M (same as source sales)

---

### Dataset 2 — `outlet_sku_monthly_demand.parquet`

**Purpose:** Fully populated monthly demand time series for every active outlet × SKU combination. This is the **primary input for the demand forecasting model**. Forecasts are produced at outlet × SKU × month grain and aggregated to territory and national level downstream. Every active outlet–SKU pair must have a row for every month in the analysis window, with zero-filled demand for inactive months.

**Primary Key:** `(outlet_id, item_code, year_month)` — unique, exhaustive for all active pairs across the full date range.

**Construction:**
1. Build the **date spine**: all `yyyy-mm` month strings from `min(document_date)` to `max(document_date)`. Use `pd.date_range(freq='MS')` then format with `strftime('%Y-%m')`.
2. Build the **active outlet–SKU spine**: all `(outlet_id, item_code)` pairs that appear at least once in `sales.parquet` with `document_type == 'invoice'`. Log the pair count at runtime.
3. Cross join active pair spine × date spine → `n_active_pairs × n_months` rows. Log estimated size before materialising — if > 10M rows, consider writing in partitions.
4. Left join actual aggregated demand onto the full grid:
   - Aggregate `base_sales_enriched` by `(outlet_id, item_code, year_month)`:
     - `net_quantity = sum(quantity)` — signed; negative net means returns exceeded invoices
     - `net_sales = sum(net_sales)` — signed
     - `gross_quantity = sum(quantity where document_type == 'invoice')`
     - `gross_sales = sum(net_sales where document_type == 'invoice')`
     - `return_quantity = abs(sum(quantity where document_type == 'return'))`
     - `return_sales = abs(sum(net_sales where document_type == 'return'))`
     - `n_invoices = count(rows where document_type == 'invoice')`
     - `n_returns = count(rows where document_type == 'return')`
5. Fill all null numeric columns with 0.
6. Left join product dimension to add `product_category`, `product_line`, `brand`.
7. Left join region dimension via the outlet's `territory_id` (first non-null `territory_id` per outlet, from `base_sales_enriched`).

**Output schema:**

| Column | Type | Notes |
|--------|------|-------|
| outlet_id | str | PK component |
| item_code | str | PK component |
| year_month | str | PK component, e.g. `2022-03` |
| territory_id | str | Outlet's territory |
| product_category | str | |
| product_line | str | |
| brand | str | |
| region | str | |
| district | str | |
| province | str | |
| net_quantity | int | sum(quantity); 0 if no activity |
| net_sales | float | sum(net_sales); 0 if no activity |
| gross_quantity | int | Invoice quantity only |
| gross_sales | float | Invoice net_sales only |
| return_quantity | int | Absolute return quantity |
| return_sales | float | Absolute return net_sales |
| n_invoices | int | Invoice row count |
| n_returns | int | Return row count |

**Estimated rows:** `n_active_pairs × n_months` — log at runtime. As a reference, if 30,000 active pairs × 84 months = 2.5M rows.

**Higher-level aggregations (derived from this dataset in downstream modules):**
- **National SKU demand**: `GROUP BY (item_code, year_month)` — used in Module 2 trend analysis
- **Territory SKU demand**: `GROUP BY (territory_id, item_code, year_month)` — used in Module 4

---

### Dataset 3 — `outlet_monthly_activity.parquet`

**Purpose:** Fully populated monthly activity record for every outlet across the full analysis window. Outlets with no transactions in a given month have an explicit zero row. This is the **base table for outlet feature engineering** and is consumed by Module 5.

**Primary Key:** `(outlet_id, year_month)` — unique, exhaustive cross product.

**Construction:**
1. Reuse the **date spine** from Dataset 2.
2. Build the **outlet spine**: all unique `outlet_id` values ever seen in `sales.parquet`.
3. Cross join date spine × outlet spine. Note: if there are N_outlets unique outlets and M months, this produces `N_outlets × M` rows. Estimate this before materialising — for 10,000 outlets × 84 months = 840,000 rows, which is manageable. If the outlet count is very large (> 50,000), filter to outlets active in the last 24 months before cross joining.
4. Left join actual aggregated activity onto the full grid:
   - Aggregate `base_sales_enriched` by `(outlet_id, year_month)`:
     - `n_invoices = count(rows where document_type == 'invoice')`
     - `gross_quantity = sum(quantity where document_type == 'invoice')`
     - `gross_sales = sum(net_sales where document_type == 'invoice')`
     - `n_returns = count(rows where document_type == 'return')`
     - `return_quantity = abs(sum(quantity where document_type == 'return'))`
     - `return_sales = abs(sum(net_sales where document_type == 'return'))`
     - `n_unique_skus = count_distinct(item_code where document_type == 'invoice')`
     - `n_unique_categories = count_distinct(product_category where document_type == 'invoice')`
     - `primary_payment_term = mode(payment_term where document_type == 'invoice')`
     - `territory_id = first(territory_id)` (outlets belong to one territory)
5. Fill all null numeric columns with 0. Fill `primary_payment_term` null with `'unknown'`.
6. Left join region dimension on `territory_id` to add `region`, `district`, `province`.

**Output schema:**

| Column | Type | Notes |
|--------|------|-------|
| outlet_id | str | PK component |
| year_month | str | PK component, e.g. `2022-03` |
| territory_id | str | |
| region | str | |
| district | str | |
| province | str | |
| n_invoices | int | 0 for inactive months |
| gross_quantity | int | 0 for inactive months |
| gross_sales | float | 0 for inactive months |
| n_returns | int | 0 for inactive months |
| return_quantity | int | 0 for inactive months |
| return_sales | float | 0 for inactive months |
| n_unique_skus | int | 0 for inactive months |
| n_unique_categories | int | 0 for inactive months |
| primary_payment_term | str | Mode payment term; 'unknown' if inactive |

**Estimated rows:** `n_unique_outlets × n_months` (compute at runtime and log)

---

### Dataset 4 — `monthly_territory_demand.parquet`

**Purpose:** Fully populated monthly demand record for every territory. Used in Module 4 geographic analysis. Derived by aggregating Dataset 2 up to territory grain, then zero-filling via cross join with the territory spine.

**Primary Key:** `(year_month, territory_id)` — unique, exhaustive cross product.

**Construction:**
1. Reuse the **date spine** from Dataset 2.
2. Build the **territory spine**: all 257 unique `territory_id` values from `region.parquet` (use the dimension table to capture territories with zero sales history).
3. Cross join date spine × territory spine → `n_months × 257` rows (e.g., 84 × 257 = 21,588 rows).
4. Aggregate `outlet_sku_monthly_demand` by `(year_month, territory_id)`:
   - `net_quantity`, `net_sales`, `gross_quantity`, `gross_sales`, `return_quantity`, `return_sales`
   - `n_invoices = sum(n_invoices)`, `n_returns = sum(n_returns)`
   - `n_outlets_active = count_distinct(outlet_id where n_invoices > 0)`
   - `n_unique_skus = count_distinct(item_code where n_invoices > 0)`
5. Left join the aggregation onto the full grid. Fill all null numeric columns with 0.
6. Left join region dimension on `territory_id` to add `region`, `district`, `province`.

**Estimated rows:** ~21,588 (84 months × 257 territories)

---

### Dataset 5 — `outlet_features.parquet`

**Purpose:** One-row-per-outlet feature matrix for K-means clustering. Derived from the last 12 months of `outlet_monthly_activity.parquet`. This is the **direct input to Module 6 clustering**.

**Primary Key:** `outlet_id` — unique.

**Construction:**
1. Define `window_start = max(year_month) - 11 months`, `window_end = max(year_month)` (12-month rolling window). Perform date arithmetic by parsing `year_month` strings back to period or datetime objects for comparison.
2. Filter `outlet_monthly_activity` to the window. Include all outlet × month rows in this window, including zero rows — they contribute to `active_months` calculation.
3. Aggregate to one row per `outlet_id`:

| Feature | Formula |
|---------|---------|
| `total_net_sales` | `sum(gross_sales)` |
| `total_quantity` | `sum(gross_quantity)` |
| `active_months` | `count(n_invoices > 0)` |
| `loyalty_ratio` | `active_months / 12` |
| `avg_txn_per_active_month` | `sum(n_invoices) / active_months` (null-safe: 0 if inactive) |
| `avg_net_sales_per_txn` | `total_net_sales / sum(n_invoices)` |
| `avg_qty_per_txn` | `total_quantity / sum(n_invoices)` |
| `n_unique_skus` | `sum(n_unique_skus)` aggregated to max distinct across window |
| `n_unique_categories` | same approach as n_unique_skus |
| `return_rate` | `sum(n_returns) / (sum(n_invoices) + sum(n_returns))` |
| `recency_months` | `window_end - max(year_month where n_invoices > 0)` in months |
| `momentum` | `sum(gross_sales in last 3 months) / sum(gross_sales in prior 3 months)` |
| `pct_cash_txn` | `count(primary_payment_term == 'cash') / active_months` |

4. Add `territory_id`, `region`, `province` from `outlet_monthly_activity` (first non-null value per outlet).
5. Add `is_active` flag: `True` if `active_months >= 1`.
6. Exclude outlets with `active_months = 0` from the clustering matrix but retain them in the file with `is_active = False`.

**Output schema:** `outlet_id`, all 13 features above, `territory_id`, `region`, `province`, `is_active`

**Estimated rows:** `n_unique_outlets` (one row per outlet ever seen in sales)

---

### Module 0 — Summary of Outputs

| File | PK | Key Purpose |
|------|----|------------|
| `base_sales_enriched.parquet` | (document_number, item_code) | Ad-hoc analysis base |
| `outlet_sku_monthly_demand.parquet` | (outlet_id, item_code, year_month) | Forecasting time series (primary grain) |
| `outlet_monthly_activity.parquet` | (outlet_id, year_month) | Outlet feature engineering |
| `monthly_territory_demand.parquet` | (year_month, territory_id) | Geographic trend analysis |
| `outlet_features.parquet` | outlet_id | Clustering input |

All files are saved to `data/Intermediate/` as `.parquet`. The script logs row counts, column counts, PK uniqueness checks, and null rates for each output file upon completion.

### Conclusion — Module 0
This preparation step is the most critical correctness gate in the entire pipeline. The zero-fill logic ensures that downstream time series models are not tricked by implicit nulls — a missing row looks the same as a zero row to a join, but means something very different to an autocorrelation model or a feature engineering window. By the end of this module, each dataset has a formally verified, exhaustive primary key (checked via `assert df.duplicated(subset=pk_cols).sum() == 0`), null rates logged, and row counts confirmed. Any downstream module that produces unexpected results should trace the root cause here first.

---

## Module 1 — Data Integration & Baseline Validation

**Purpose:** Confirm all three source tables join cleanly and the base analytical dataset is internally consistent. Establishes the verified analytical foundation before any statistical analysis begins.

**Input:** `data/input/processed/` (three raw processed parquets)
**Uses:** `base_sales_enriched.parquet` from Module 0

### Steps

**Join Integrity**
1. Left join `sales` → `product` on `item_code`. Record count of unmatched item codes — any null `product_category` after the join indicates orphaned sales records.
2. Left join result → `region` on `territory_id`. Record count of unmatched territory IDs.
3. Compute match rate for both joins: `matched_rows / total_rows × 100`. A rate below 98% warrants investigation before proceeding.
4. Cross-check unique counts: `n_unique(item_code)` in sales must be ≤ 50. `n_unique(territory_id)` in sales must be ≤ 257.

**Temporal Baseline**
5. Establish the analysis window: `min(document_date)`, `max(document_date)`, total calendar months.
6. Plot row count by calendar month — confirm no complete months are missing. A sudden drop may indicate a data extraction gap rather than genuine demand decline.
7. Confirm all 12 calendar months are represented in at least one year.

**Returns Baseline**
8. Verify that the sign convention from Pipeline 2 is intact: all rows where `document_type == 'return'` must have `quantity < 0` and `net_sales < 0`. Flag any exceptions as a pipeline integrity failure — do not fix them here; escalate to Pipeline 2.
9. Compute overall return rate: `abs(sum(quantity where document_type == 'return')) / sum(quantity where document_type == 'invoice')`.
10. Break down return rate by year — a rising trend signals systemic product or process issues that should be escalated before the forecasting pipeline is built.

### Conclusion — Module 1

This module answers the question: *is the data fit for analysis?* The conclusion should state definitively:
- **Join completeness**: what percentage of sales rows matched to a product and a territory. Any orphaned rows are excluded from downstream analysis and quantified.
- **Date coverage**: the exact analysis window (e.g., January 2015 – December 2022) and confirmation that no full months are missing. This defines the maximum training window available for the forecasting model.
- **Return integrity**: pass or fail on the sign-convention check, and the baseline return rate. A return rate of, for example, 4.1% means ~1 in 24 gross units is returned — a known cost to factor into demand net figures.
- **Readiness verdict**: explicit go / no-go statement before proceeding. If any join match rate falls below 98% or the sign-convention check fails, the root cause must be resolved in the raw processing pipeline before EDA proceeds.

---

## Module 2 — Temporal & Demand Analysis

**Purpose:** Characterise demand dynamics at outlet × SKU × month grain and at national aggregation — trend, seasonality, stationarity, and volatility. These properties directly determine which forecasting model class is appropriate and set the parameters for the buffer mechanism.

**Input:** `outlet_sku_monthly_demand.parquet` (aggregated to national SKU grain for time series tests), `base_sales_enriched.parquet`

### Steps

**National Trend**
1. Aggregate `net_quantity` and `net_sales` by `year_month` across all outlets and SKUs (from `outlet_sku_monthly_demand`).
2. Plot the monthly time series. Overlay 3-month and 12-month centred moving averages to separate signal from noise.
3. Compute MoM and YoY growth rates. Plot both — MoM exposes volatility, YoY reveals structural trend.

**Seasonality Decomposition**
4. Apply STL decomposition (Seasonal-Trend decomposition using LOESS) with period = 12 on the national monthly `net_quantity` series.
   - Plot trend, seasonal, and residual components separately.
   - Compute seasonal strength: `Var(seasonal) / (Var(seasonal) + Var(residuals))`. Values > 0.6 indicate seasonality must be modelled explicitly.
5. Month-of-year heatmap (`month × year`) of volume — visually confirm which months are structurally high or low.
6. Compute the seasonal index per month: `mean(month_i_volume) / mean(all_months_volume)`. Index > 1.2 means a 20%+ structural uplift for that month.

**Stationarity Testing**
7. Run the Augmented Dickey-Fuller (ADF) test on the national monthly `net_quantity` series.
   - H₀: series has a unit root (non-stationary). Reject at p < 0.05.
   - If non-stationary, apply first-order differencing and re-test. Report the integration order d.
8. Run the KPSS test (H₀: series is stationary) as a complementary check. Conflicting results between ADF and KPSS indicate a fractionally integrated or trend-stationary series.

**Autocorrelation Structure**
9. Plot ACF and PACF for the national monthly `net_quantity` series (and first-differenced series if needed).
   - Slow ACF decay + PACF cutoff at lag p → AR(p). Sharp ACF cutoff at lag q → MA(q).
10. Run the Ljung-Box test at lags 6 and 12. p < 0.05 means exploitable autocorrelation structure exists — the series is not white noise.

**Returns Over Time**
11. Plot monthly return rate. Compute the 95th percentile threshold — months above this are anomaly candidates requiring investigation.

**SKU-Level Demand Analysis**
12. From `outlet_sku_monthly_demand`, aggregate to `(item_code, year_month)` by summing `net_quantity`. Per SKU compute:
    - Active months (months where national `net_quantity > 0`)
    - Demand interval: mean gap between non-zero months (Croston's method input)
    - CV: `std(net_quantity) / mean(net_quantity)` over active months only
13. Segment SKUs by demand pattern:
    - **Continuous**: active ≥ 80% of months, CV < 0.5 → ARIMA / ETS class
    - **Intermittent**: active 20–80%, or CV 0.5–1.0 → Croston / SBA class
    - **Lumpy**: active < 20%, or CV > 1.0 → manual review or ADIDA
14. Plot the count of SKUs in each demand class. This determines the forecasting model portfolio.

**Outlet–SKU Grain Characterisation**
15. From `outlet_sku_monthly_demand`, compute per outlet–SKU pair:
    - Active months and CV at pair level
    - Fraction of pairs that are Continuous / Intermittent / Lumpy
    This gives the true distribution of demand sparsity at the grain forecasts will be produced at.

**Demand Volatility for Buffer Sizing**
16. Segment SKUs by CV tier: Low (< 0.3), Medium (0.3–0.6), High (> 0.6).
17. Plot the CV distribution. Compute 90th percentile CV as the worst-case assumption for buffer sizing.
18. The safety stock formula `SS = Z × σ_demand × √lead_time` requires `σ_demand` per SKU — this is the EDA output that feeds the buffer model directly.

### Conclusion — Module 2

This module answers the question: *what is the structural behaviour of demand and how does it vary by SKU and outlet?* The conclusion should state:
- **Trend direction**: whether national demand is growing, flat, or declining over the analysis period, supported by YoY growth rates.
- **Seasonality verdict**: whether seasonality is strong enough (strength > 0.6) to require explicit seasonal modelling. Name the peak and trough months from the seasonal index.
- **Stationarity verdict**: ADF and KPSS results. State the integration order and whether differencing is needed before ARIMA-class models. This is a go/no-go decision for model selection.
- **Autocorrelation structure**: the likely AR and MA orders suggested by ACF/PACF, as a preliminary model specification.
- **SKU demand class mix**: how many SKUs fall into each of the three demand classes at national grain, and how that translates to the outlet–SKU pair level. The pair-level sparsity directly determines how many pairs require intermittent/lumpy methods.
- **Buffer implications**: the 90th percentile CV and what it means for safety stock — e.g., high-CV SKUs will require 2–3× more safety stock than low-CV SKUs at the same service level.

---

## Module 3 — Product Portfolio Analysis

**Purpose:** Identify revenue concentration, mix dynamics, and return risk by product. Informs SKU prioritisation for the forecasting model and the portfolio strategy slide in the CEO presentation.

**Input:** `base_sales_enriched.parquet`, `outlet_sku_monthly_demand.parquet`

### Steps

**Revenue & Volume Contribution**
1. Aggregate `gross_sales` by `item_code` from `outlet_sku_monthly_demand`. Rank all SKUs by total gross sales. Compute cumulative revenue share.
2. Pareto chart — identify the SKU count covering 80% of revenue. Segment:
   - **Core**: top 80% revenue — must-forecast SKUs
   - **Growth**: next 15% — forecast with simpler models
   - **Long Tail**: bottom 5% — low ROI to forecast individually; consider aggregate or intermittent methods
3. Compute the Herfindahl-Hirschman Index (HHI) at SKU, product line, and brand level:
   - `HHI = Σ (revenue_share_i)²`. HHI > 0.25 = high concentration (monopolistic territory).
   - High HHI means the business faces significant revenue risk if one SKU underperforms — a key CEO message.

**Growth Rates by Product**
4. Compute CAGR per product line: `(end_volume / start_volume)^(1/n_years) - 1`.
5. 2×2 strategic matrix: CAGR (x-axis) vs. revenue share (y-axis), bubble size = absolute volume.
   - Top-right: Protect and invest. Top-left: Defend. Bottom-right: Nurture. Bottom-left: Review or exit.

**Mix Shift Over Time**
6. 100% stacked bar: product category share of volume by year — identify structural share gains and losses.
7. Brand share by year — given Brand_1 represents 88% of the SKU catalogue, monitor whether non-Brand_1 items are gaining traction.

**Return Analysis by Product**
8. Return rate per product category and brand: `return_quantity / gross_quantity` aggregated from `outlet_sku_monthly_demand`.
9. Z-score flag: categories or brands with return rate > 2 standard deviations above the mean.
10. Chi-square test (contingency table: invoice vs. return rows × product category). H₀: return rate is independent of category. p < 0.05 means category-specific return risk exists.

**SKU Demand Continuity**
11. From `outlet_sku_monthly_demand`, classify each SKU as Continuous / Intermittent / Lumpy (aligned with Module 2 taxonomy).
12. Summarise by product category — identify categories dominated by Lumpy SKUs, as these inflate safety stock requirements disproportionately.

### Conclusion — Module 3

This module answers: *which products drive the business, where are the growth opportunities, and where is the risk concentrated?* The conclusion should state:
- **Concentration risk**: HHI score at SKU and brand level, and what percentage of revenue is carried by the top N SKUs. High HHI is a direct business risk — if the top 5 SKUs account for 60% of revenue, any supply disruption has outsized impact.
- **Strategic portfolio quadrants**: name the product lines in each quadrant of the 2×2 matrix. "Prod_line3 is a Defend asset — high share but declining CAGR. Prod_line7 is a Nurture candidate — low share but strong growth."
- **Mix shift finding**: whether the product category or brand mix is stable or shifting. A shift away from the core category is a structural risk; a shift toward Growth lines is an opportunity.
- **Return risk**: which categories are statistically elevated in return rate (chi-square result) and the magnitude of the excess rate. High-return SKUs inflate gross demand signals and must be net-adjusted in the forecasting model.
- **Forecast prioritisation**: which SKUs are Core and Continuous — these get the full ARIMA/ETS treatment. Which are Intermittent or Long Tail — these get Croston or are aggregated.

---

## Module 4 — Geographic Analysis

**Purpose:** Quantify territorial demand patterns, concentration, and growth disparities. Provides the geographic context for the CEO presentation and informs the cluster-to-geography cross-tab in Module 6.

**Input:** `monthly_territory_demand.parquet`, `outlet_sku_monthly_demand.parquet`

### Steps

**Revenue Distribution**
1. Aggregate `gross_sales` and `gross_quantity` by province, region, and district from `monthly_territory_demand`.
2. Bar chart: revenue share by province. Compute CR3: `sum(top 3 provinces) / total`. CR3 > 0.6 indicates high geographic dependency.
3. Gini coefficient of revenue across territories: `G = (2 × Σ i × revenue_i) / (n × Σ revenue_i) - (n+1)/n`. Lorenz curve visualisation. Gini approaching 1 = extreme concentration.

**Territory-Level Growth**
4. YoY revenue growth per territory for each consecutive year pair from `monthly_territory_demand`.
5. Flag top 10 and bottom 10 growing territories. Cross-check bottom 10 against return rates and outlet counts.
6. One-way ANOVA: do mean monthly `gross_sales` values differ significantly across regions?
   - H₀: all regional means are equal. Reject at p < 0.05.
   - If rejected: Tukey HSD post-hoc to identify which region pairs are significantly different.
   - This statistically justifies region-specific demand models and targets, rather than a uniform national target.

**Route & Outlet Density**
7. Count distinct outlets and total volume per `route_id` from `base_sales_enriched`. Compute revenue-per-outlet per route.
8. Spearman rank correlation: outlet count per territory vs. territory revenue. If ρ < 0.7, outlet density alone does not explain revenue — outlet quality/behaviour differences dominate.

**Payment Geography**
9. Cash vs. credit mix by region. Chi-square test: H₀: payment term is independent of region. p < 0.05 means payment behaviour is geographically segmented — relevant for credit risk and sales force incentive design.

### Conclusion — Module 4

This module answers: *where is demand concentrated, where is it growing, and are geographic units meaningfully different from each other?* The conclusion should state:
- **Geographic concentration**: the Gini coefficient and CR3 value. For example, "Revenue is highly concentrated (Gini = 0.71) — the top 3 provinces account for 58% of total revenue. This creates significant supply chain and business continuity risk."
- **Regional growth leaders and laggards**: name the top 3 and bottom 3 regions by CAGR. Regions in structural decline warrant investigation into whether this is a distribution coverage issue or a genuine market contraction.
- **ANOVA result**: whether regional mean sales are statistically different (p-value and F-statistic). If yes, state that this justifies building region-specific demand models rather than applying a national-level model uniformly.
- **Tukey HSD pairs**: which specific region pairs are significantly different — e.g., "Region 5 and Region 6 have significantly higher mean monthly sales than Region 1 and Region 8 (p < 0.01), justifying distinct volume targets."
- **Outlet density insight**: whether the Spearman correlation result suggests that outlet count or outlet quality drives revenue. Low correlation means the business should focus on upgrading existing outlets rather than expanding to new ones — a direct input to the CEO recommendation.
- **Payment geography risk**: if payment term distribution is geographically heterogeneous, flag the highest cash-concentration regions as credit risk clusters.

---

## Module 5 — Outlet Behavioural Profiling

**Purpose:** Engineer a clean, statistically validated outlet feature matrix for K-means clustering. Features must be scaled, non-collinear, and free of degenerate distributions. The output of this module is the direct input to Module 6.

**Input:** `outlet_monthly_activity.parquet`, `outlet_features.parquet` (from Module 0)

### Feature Set (Rolling 12-Month Window)

All features are pre-computed in `outlet_features.parquet` (Module 0 Dataset 5). This module validates and prepares those features for clustering.

| Feature | Definition | Signal |
|---------|-----------|--------|
| `total_net_sales` | Sum of gross_sales | Outlet size |
| `total_quantity` | Sum of gross_quantity | Volume throughput |
| `active_months` | Count of months with ≥1 invoice | Loyalty / consistency |
| `loyalty_ratio` | active_months / 12 | Activity rate (0–1) |
| `avg_txn_per_active_month` | Invoice count / active_months | Purchase frequency |
| `avg_net_sales_per_txn` | total_net_sales / invoice count | Basket value |
| `avg_qty_per_txn` | total_quantity / invoice count | Basket volume |
| `n_unique_skus` | Distinct SKUs purchased | Product breadth |
| `n_unique_categories` | Distinct categories purchased | Category diversity |
| `return_rate` | Return rows / total rows | Quality / satisfaction |
| `recency_months` | Months since last invoice | Churn risk |
| `momentum` | Net sales last 3m / prior 3m | Growth trajectory |
| `pct_cash_txn` | Cash transactions / active months | Payment behaviour |

> **Active outlet:** ≥1 invoice in the last 12 months. Churned outlets are excluded from clustering but retained in the file with `is_active = False`.

### Statistical Validation

**Normality Testing**
1. Shapiro-Wilk (n ≤ 5,000) or D'Agostino-Pearson (n > 5,000) on each numeric feature.
   - H₀: feature is normally distributed. Expected: most will fail — skewed distributions are expected.
   - This justifies log transformation before clustering (K-means is sensitive to scale and skew via Euclidean distance).

**Outlier Detection**
2. IQR fence at 3×: `lower = Q1 - 3×IQR`, `upper = Q3 + 3×IQR`.
3. Flag outlets breaching 3+ features as structural outliers. Exclude from clustering but analyse separately — they may represent mega-outlets or data entry errors.
4. Outlier rate per feature: > 5% indicates a severely distorted distribution requiring transformation.

**Transformation**
5. Log-transform right-skewed features (`total_net_sales`, `total_quantity`, `avg_net_sales_per_txn`, `avg_qty_per_txn`): apply `log(x + 1)`. Re-run normality test to confirm improvement.
6. Winsorise `momentum` at 1st and 99th percentile — extreme ratios from near-zero denominators must not dominate cluster distances.
7. Bounded features (`loyalty_ratio`, `return_rate`, `pct_cash_txn`) require no transformation; [0,1] scale is already appropriate.

**Multicollinearity**
8. Pearson correlation matrix post-transformation. Heatmap. Flag |r| > 0.85 pairs.
9. Compute VIF for all features. Iteratively drop the highest VIF feature until all VIF < 5.
10. Document the final retained feature set and dropped features with rationale.

**Final Scaling**
11. Apply `StandardScaler` (zero mean, unit variance) to all retained features.
12. Verify: all feature means ≈ 0, all standard deviations ≈ 1.

### Conclusion — Module 5

This module answers: *what does the outlet population look like, and is the feature set clean enough to produce meaningful clusters?* The conclusion should state:
- **Outlet population size**: total active outlets in the 12-month window vs. churned outlets. The churn count is itself a business metric — outlets with zero activity in 12 months represent lost distribution points.
- **Structural outliers**: how many outlets were excluded from clustering as mega-outlets or data anomalies, and what their aggregate revenue share represents. A small number of extreme outliers can account for a disproportionate share of revenue.
- **Normality results**: which features failed the normality test and whether log-transformation resolved the skew. Quantify the improvement using the skewness coefficient before and after transformation.
- **Dropped features**: which features were removed via VIF iteration and what that means — e.g., "total_quantity and total_net_sales were collinear (r = 0.94); total_quantity was dropped as total_net_sales carries more business meaning."
- **Final feature count**: the number of features entering the clustering model and their names. This is the confirmed input specification for Module 6.
- **Key distribution observations**: any notable patterns in the feature distributions — e.g., "loyalty_ratio is bimodally distributed, with a large cluster of outlets near 0.1 (sporadic) and another near 0.9 (loyal). This strongly suggests at least 2 natural outlet cohorts."

---

## Module 6 — K-Means Clustering EDA

**Purpose:** Determine the optimal number of outlet clusters using multiple statistical criteria, validate cluster quality, visualise the structure, profile each cluster for business interpretation, and apply sub-clustering within each primary cluster.

**Input:** Scaled outlet feature matrix (output of Module 5 `StandardScaler` step)

### 6.1 — Optimal K Selection

Run K-means (`n_init = 20`, `random_state = 42`) for k = 2 through k = 15. Record:

| Metric | Definition | Optimise By |
|--------|-----------|-------------|
| Inertia (WCSS) | Sum of squared distances to centroids | Elbow — largest rate-of-change kink |
| Silhouette Score | Mean `(b-a)/max(a,b)` per sample | Maximise (range: -1 to 1) |
| Davies-Bouldin Index | Mean ratio of intra-cluster spread to inter-cluster distance | Minimise |
| Calinski-Harabasz Index | Between-cluster variance / within-cluster variance | Maximise |
| Gap Statistic | Observed WCSS vs. expected under uniform null, B = 10 bootstraps | First k where `gap(k) ≥ gap(k+1) - std(k+1)` |

1. Plot all 5 metrics vs. k on a multi-panel figure.
2. Select k where ≥ 3 of 5 metrics agree — this is the primary candidate.
3. Test k ± 1 for sensitivity: do cluster profiles change meaningfully? A robust result is stable across k ± 1.
4. Document the selected k and the metric evidence.

### 6.2 — Cluster Quality Validation

5. Per-sample silhouette plot for the selected k (samples grouped by cluster, sorted by silhouette value within each group).
   - Clusters with many samples below 0.2 are poorly separated — consider merging or revisiting the feature set.
   - Target: average silhouette > 0.35.
6. WCSS per individual cluster — large imbalance in WCSS values across clusters signals that some clusters are internally heterogeneous.
7. Cluster size check: any cluster with < 3% of outlets is likely a noise cluster. Investigate its members — is it a genuine micro-segment (e.g., direct distributors) or an artefact of outliers?
8. Bootstrap stability: resample the feature matrix 20 times at 80%, re-run K-means, compute Jaccard similarity of assignments per cluster vs. full-data fit. Mean Jaccard > 0.75 = stable.

### 6.3 — Visualisation

9. **PCA biplot**: reduce to 2 principal components, plot coloured by cluster. Overlay feature loading arrows. Report PC1 + PC2 explained variance — if < 50%, add a 3D plot with PC3.
10. **t-SNE / UMAP**: non-linear 2D embedding (t-SNE perplexity = 30 or UMAP n_neighbors = 15). Colour by cluster. Cleaner boundaries here than in PCA implies non-linear cluster structure.
11. **Parallel coordinates plot**: all scaled features as parallel axes, one line per outlet, coloured by cluster. Most visually separated axes identify the features that most strongly differentiate clusters.

### 6.4 — Cluster Profiling

12. Per cluster: mean, median, and standard deviation of every feature.
13. Cluster profile table: features as rows, clusters as columns, showing medians.
14. Radar chart per cluster: normalised medians on each feature axis — the behavioural "fingerprint".
15. Assign a business label to each cluster. Examples:
    - "High-Value Loyal": high `total_net_sales`, `loyalty_ratio` ≈ 1.0, high `n_unique_skus`
    - "High-Frequency Low-Basket": high `avg_txn_per_active_month`, low `avg_net_sales_per_txn`
    - "Bulk Occasional Buyers": high `avg_qty_per_txn`, low `active_months`
    - "Churning Low-Activity": high `recency_months`, low `loyalty_ratio`
    - "Cash-Dominant Growth": high `pct_cash_txn`, positive `momentum`
16. Cluster × region cross-tab heatmap. Chi-square test: H₀: cluster assignment is independent of region. p < 0.05 = geographically concentrated clusters.

### 6.5 — Sub-Clustering

17. For each primary cluster, apply the same process (Steps 6.1–6.4) to the cluster's member outlets in isolation.
    - K search range: k = 2 to 6 (smaller range appropriate for subsets).
    - Same 5-metric selection criteria.
18. If Silhouette < 0.25 for all k > 1 within a cluster, the cluster is already homogeneous — no sub-clustering needed. Document this finding.
19. Build the full cluster hierarchy table: primary cluster → sub-clusters, with member count and median feature profile at each level.

### Conclusion — Module 6

This module answers: *how many meaningfully distinct outlet cohorts exist, what are their behavioural fingerprints, and are they geographically structured?* The conclusion should state:
- **Selected k and justification**: the optimal number of clusters and which of the 5 metrics supported the choice. E.g., "k = 4 was selected — Silhouette peaked at 0.48, Davies-Bouldin was minimised, and the Gap Statistic confirmed k = 4 as the first stable solution."
- **Cluster quality assessment**: average silhouette score, WCSS balance, and bootstrap Jaccard results. Explicitly state whether the clustering is reliable enough to base business decisions on.
- **Cluster business labels and profiles**: name each cluster with its label and top 3 distinguishing features. E.g., "Cluster 2 (High-Value Loyal, n = 1,840 outlets) is defined by loyalty_ratio ≈ 0.95, total_net_sales 3.2× the population median, and n_unique_skus = 18 — these are the anchor accounts of the distribution network."
- **Geographic concentration**: chi-square result on cluster × region. If significant, state which clusters are geographically concentrated and what this implies — geographically concentrated clusters suggest that distribution strategy (not just outlet behaviour) shapes purchasing patterns.
- **Sub-clustering findings**: which primary clusters could be meaningfully subdivided and what the sub-clusters represent. If a primary cluster breaks into two distinct sub-types, name them and describe the split.
- **Forecasting implication**: directly state that individual demand models will be fitted per cluster (not per outlet), and that the cluster typology justifies this — behavioural heterogeneity across clusters is large enough that a single national model would systematically over-forecast some clusters and under-forecast others.

---

## Module 7 — Within-Cluster Outlet Maximum Potential

**Purpose:** Within each K-means cluster, identify the top-performing outlets as the peer ceiling benchmark and quantify the total revenue uplift opportunity for underperforming outlets. Cluster-level benchmarking produces tighter, more credible targets than region-level comparisons because behavioural peers — not just geographic neighbours — define what is achievable.

**Input:** `outlet_features.parquet`, cluster assignments from Module 6

### Peer Group Definition
Peer groups are defined at the **cluster level**. Supplementary region-level benchmarking is retained for geographic decomposition of the opportunity.

### Steps

**Tier Segmentation Within Each Cluster**
1. Within each primary cluster, rank all outlets by `total_net_sales` (descending).
2. Assign tiers:
   - **Top 30%**: ceiling benchmarks — what is achievable within this behavioural cohort
   - **Middle 60%**: core performing outlets — primary volume push targets
   - **Bottom 10%**: underperformers — candidates for active intervention or removal from distribution

**Tier Profiling**
3. Per tier per cluster: mean and median of `total_net_sales`, `total_quantity`, `loyalty_ratio`, `avg_net_sales_per_txn`, `n_unique_skus`, `return_rate`, `recency_months`.
4. Side-by-side tier comparison table per cluster — quantifies the behavioural gap between underperformers and the ceiling group within the same cohort.
5. Mann-Whitney U test: compare `total_net_sales` distributions between Top 30% and Bottom 10% within each cluster. H₀: the two groups come from the same distribution. p < 0.05 confirms statistically distinct tiers.

**Ceiling Benchmark & Uplift Estimation**
6. Per cluster: define the ceiling as the **median `total_net_sales` of the Top 30%** — the median is robust to extreme performers inflating the target.
7. Per non-Top-30% outlet:
   - Raw uplift: `cluster_ceiling - actual_net_sales`
   - Percentage gap: `(cluster_ceiling - actual) / actual × 100`
8. Aggregate total addressable uplift per cluster: sum of raw uplift for all Middle 60% + Bottom 10% outlets.
9. Rank clusters by total addressable uplift — the highest-uplift cluster is the highest-priority intervention target.

**Cluster vs. Region Comparison**
10. Compute both the cluster-ceiling gap and the region-ceiling gap (from Module 4 benchmarks) for each outlet.
    - Cluster gap < region gap: the outlet is underperforming even relative to its behavioural peers — highest-confidence intervention signal.
    - Cluster gap > region gap: the region has a lower structural ceiling — geographic factors limit the outlet's potential.

**Visualisation**
11. Box plot per cluster: `total_net_sales` distribution with Top 30% threshold line.
12. Scatter plot per cluster: `loyalty_ratio` vs. `total_net_sales`, coloured by tier — tests whether underperformance is driven by activity frequency vs. basket size.
13. Bubble chart for CEO: x = cluster label, y = total addressable uplift, bubble size = count of non-Top-30% outlets.

**Sub-Cluster Potential**
14. Repeat tier segmentation and uplift estimation within each sub-cluster. Sub-cluster uplift = conservative estimate. Primary-cluster uplift = upper bound.

### Conclusion — Module 7

This module answers: *how large is the revenue opportunity from unlocking underperforming outlets, and which clusters should be prioritised?* The conclusion should state:
- **Total addressable uplift**: the aggregate revenue opportunity if all Middle 60% and Bottom 10% outlets reached their cluster ceiling. State this as an absolute number and as a percentage of current total revenue. This is the headline number for the CEO presentation.
- **Priority clusters**: rank clusters by total addressable uplift. For the top 2 clusters, describe what the uplift looks like in behavioural terms — e.g., "Cluster 3 (Bulk Occasional Buyers) has the largest uplift pool at X revenue units, concentrated in outlets with high basket size but low activity. The intervention is frequency-driven: increasing visit frequency from 4 to 7 active months would close the gap."
- **Bottom 10% characterisation**: describe the typical behavioural profile of Bottom 10% outlets across clusters. Is underperformance driven primarily by low activity (recency, loyalty_ratio), low basket size, or high return rates? The root cause determines the intervention.
- **Sub-cluster vs. primary-cluster uplift range**: the conservative (sub-cluster) vs. upper-bound (primary cluster) uplift estimates per cluster, giving the CEO a range rather than a point estimate — more defensible in a board presentation.
- **Actionable recommendation**: for each cluster, one specific intervention recommendation based on the tier comparison. For example: "For the High-Frequency Low-Basket cluster, the ceiling gap is driven by low SKU breadth — Bottom 10% outlets purchase on average 4 SKUs vs. 14 in the Top 30%. A targeted cross-selling programme focused on introducing 3 additional SKUs could close 40% of the gap."

---

## Execution Order

```
pipelines/3_eda/
├── 00_dataset_preparation.py               ← Run first; builds all analytical datasets
├── 01_data_integration.ipynb               ← Join validation, returns audit
├── 02_temporal_demand_analysis.ipynb       ← STL, ADF/KPSS, ACF/PACF, SKU demand table
├── 03_product_portfolio_analysis.ipynb     ← Pareto, HHI, CAGR matrix, chi-square returns
├── 04_geographic_analysis.ipynb            ← Gini, ANOVA, Tukey HSD, payment chi-square
├── 05_outlet_profiling.ipynb               ← Normality, VIF, StandardScaler, feature matrix
├── 06_outlet_clustering_eda.ipynb          ← Optimal k, silhouette, t-SNE, sub-clusters
└── 07_outlet_performance_benchmarking.ipynb ← Within-cluster tiers, uplift estimation
```

---

## Key Analytical Decisions & Assumptions

| Decision | Rationale |
|----------|-----------|
| Zero-fill all primary key tables in Module 0 | Missing rows = implicit zeros confuse time series models and feature engineering windows |
| Use `data/Intermediate/` for analytical datasets | Separates raw processed data from analysis-ready structures; config-driven path |
| No return re-handling in Module 0 | Pipeline 2 already applies negative signs to return `quantity` and `net_sales`; re-handling would double-count |
| Forecast grain: outlet × SKU × month | Enables granular accuracy measurement and per-outlet plans; aggregate to territory/national for reporting |
| Active outlet–SKU pairs as cross-join spine | Avoids exploding the dataset with outlet–SKU combinations that were never transacted |
| `year_month` stored as `str` in `yyyy-mm` format | Avoids Period serialisation issues in Parquet; simple string comparison is sufficient for sorting and filtering |
| 12-month rolling window for outlet features | Normalises for varying outlet tenure; focuses on recent behaviour |
| Monthly forecast grain | Client requirement; sub-monthly overfits seasonal noise |
| K-means with `n_init = 20`, `random_state = 42` | Reproducible results; multiple random starts reduce centroid instability (from conf.yml) |
| 5-metric optimal-k selection | No single metric is sufficient; consensus across metrics reduces the risk of over- or under-clustering |
| Cluster-level peer groups for benchmarking | Behavioural peers produce tighter and more credible ceilings than geographic peers alone |
| Bottom 10% defined within each cluster | Peer-relative underperformance is more actionable than absolute thresholds |
| Log transform before K-means | Euclidean distance is sensitive to scale and outliers; log reduces both |
| VIF < 5 for feature retention | Removes redundant dimensions that inflate distances along shared axes |
| Sub-cluster potential as conservative estimate | Tighter peer groups produce lower, more defensible uplift estimates |

---

## Statistical Tests Summary

| Module | Test | H₀ | Action if Rejected |
|--------|------|-----|-------------------|
| 2 | ADF | Series has unit root (non-stationary) | First-difference before ARIMA |
| 2 | KPSS | Series is stationary | Difference or use trend model |
| 2 | Ljung-Box (lags 6, 12) | Residuals are white noise | Model autocorrelation structure |
| 3 | Chi-square | Return rate ⊥ product category | Apply category-specific return adjustments |
| 4 | One-way ANOVA | Regional mean sales are equal | Justify region-specific targets |
| 4 | Tukey HSD | Pairwise regional means are equal | Identify diverging region pairs |
| 4 | Chi-square | Payment term ⊥ region | Flag geographic credit risk segments |
| 5 | Shapiro-Wilk / D'Agostino | Feature is normally distributed | Apply log transform |
| 6 | Chi-square | Cluster assignment ⊥ region | Confirm geographic-behavioural correlation |
| 7 | Mann-Whitney U | Top 30% and Bottom 10% from same distribution | Confirm tier statistical distinctness |

---

## Downstream Handoffs

| EDA Output | File | Feeds Into |
|------------|------|-----------|
| Outlet × SKU × month demand table + demand class taxonomy | `outlet_sku_monthly_demand.parquet` | Pipeline 4: Forecasting model class selection |
| σ_demand per SKU + CV tiers | Derived in Module 2 | Pipeline 5: Safety stock / buffer model |
| Pareto segments, HHI, CAGR 2×2 matrix | Derived in Module 3 | CEO Presentation: portfolio strategy |
| Gini, ANOVA results, growth leaders/laggards | Derived in Module 4 | CEO Presentation: geographic opportunity |
| Scaled outlet feature matrix | Derived in Module 5 | Module 6: K-means clustering input |
| Cluster assignments + labels + sub-cluster hierarchy | Derived in Module 6 | Pipeline 4: Per-cluster individual demand models; CEO clustering slide |
| Within-cluster tier rankings + total addressable uplift | Derived in Module 7 | CEO Presentation: volume push recommendation; Pipeline 6: Distribution strategy |
