# [Pipeline 1] Data Quality Report

**Date:** 2026-05-01
**Pipeline:** Pipeline 1 — Data Quality Assessment across Sales and Mapping Datasets
**Output file:** `docs/1_dq/dq_report.md`

---

## Introduction — Why Data Quality Checks Matter

Before any analysis, modelling, or reporting can be trusted, the underlying data must be verified for correctness, completeness, and consistency. Skipping this step routinely leads to silent errors: models trained on null-inflated features that degrade accuracy, aggregations distorted by extreme outliers, and business decisions built on counts that exclude entire categories due to undetected join failures.

A structured DQ check surfaces these risks early, when they are cheapest to fix. It establishes a known baseline — shape, null rates, distributions, and identifier integrity — that becomes a reference point for every downstream transformation. It also forces explicit decisions: is a 4.7% null rate in `PaymentTerm` a business rule or a pipeline gap? Is Brand_1 truly 88% of the product catalogue, or is data from other brands simply missing? Answering these questions upfront prevents assumptions from silently propagating through the pipeline.

---

## Overview

Three raw datasets were assessed: the invoice-level sales transaction file (`invoice_level_sales.csv`), the product dimension table (`Product Mapping.csv`), and the geographic dimension table (`Region Mapping.csv`). Each notebook followed the same six-step framework — shape and dtype profiling, null analysis, numeric statistics, categorical distribution review, automated issue detection, and remedial action planning. The outputs document the current health of each dataset and recommend concrete next steps before any joins or feature engineering begins.

---

## Dataset 1 — invoice_level_sales.csv

**Source:** `data/input/raw/invoice_level_sales.csv`
**Size:** 6,799,893 rows × 12 columns

### Working Assumptions

- `documentDate` is expected to be parseable as a date despite being stored as `str`.
- `DocumnetNumber` (note the typo in the source column name) is an invoice identifier and should not be used as a modelling feature.
- `OutletID` and `RouteID` are high-cardinality categorical identifiers used for joins, not modelling.
- The 4.71% null rate in `PaymentTerm` is assumed to be a pipeline gap rather than a structural business rule.
- Extreme `NetSales` and `Quantity` values are assumed to require investigation before being accepted as legitimate.

### Workflow Structure

1. Load CSV and confirm shape (6,799,893 × 12).
2. Profile column dtypes — identified `documentDate` as `str`, `TerritoryID` and `Quantity` as `int64`, `NetSales` and `Discount` as `float64`, remainder as `str`/`object`.
3. Null analysis — only `PaymentTerm` had missing values: 320,181 nulls (4.71%).
4. Descriptive statistics for numeric columns (`TerritoryID`, `NetSales`, `Quantity`, `Discount`).
5. Categorical distribution review for low-cardinality columns (`DocumentType`, `IsDirectDistributor`, `PaymentTerm`).
6. Automated DQ issue detection — 7 issues identified across 4 columns.
7. Remedial action table — one recommended action per issue.

### Key Decisions

- **Separate DQ from transformation:** The DQ notebook intentionally does not modify the data. All remedies are recommendations for a downstream cleaning step, preserving the raw source for reproducibility.
- **IQR-based outlier detection for NetSales and Quantity:** Chosen over simple z-score because the distributions are heavily right-skewed (mean/median ratios of 3.81 and 4.33 respectively), making z-score thresholds misleading.
- **Medium severity for PaymentTerm nulls:** 4.71% is below the 5% warning threshold but warrants investigation because the column is used for payment behaviour analysis, and missingness may be non-random.

### Issue Summary

| Column | Issue | Severity |
|--------|-------|----------|
| `PaymentTerm` | 4.71% missing values | Medium |
| `DocumentType` | Imbalanced — Invoice is 95.9% of values | Medium |
| `IsDirectDistributor` | Imbalanced — NO is 99.4% of values | Medium |
| `NetSales` | Potential outliers (beyond 3×IQR) | Medium |
| `NetSales` | High right skew (mean/median = 3.81) | Low |
| `Quantity` | Potential outliers (beyond 3×IQR) | Medium |
| `Quantity` | High right skew (mean/median = 4.33) | Low |

### Notes / Additional Context

- No High-severity issues were found; all issues are Medium or Low.
- `DocumnetNumber` contains a source-system typo — rename during ingestion.
- High-cardinality ID columns (`DocumnetNumber`, `OutletID`, `RouteID`) should be excluded from ML features unless used explicitly for lookups.

---

## Dataset 2 — Product Mapping.csv

**Source:** `data/input/raw/Product Mapping.csv`
**Size:** 50 rows × 4 columns

### Working Assumptions

- `Item Code` is a unique product identifier and should not be used as an ML feature.
- The anonymised labels (`Cat_1`–`Cat_7`, `Prod_line1`–`Prod_line26`, `Brand_1`–`Brand_6`) represent real categories masked for the assessment.
- Brand_1 dominance (88%) is assumed to warrant validation rather than being accepted as representative of the full catalogue.

### Workflow Structure

1. Load CSV and confirm shape (50 × 4).
2. Profile dtypes — all four columns are `str`.
3. Null analysis — zero nulls across all columns.
4. Categorical distributions for all four columns (all have ≤ 50 unique values).
5. Automated DQ issue detection — 1 low-severity issue flagged (`Item Code` high cardinality ratio).
6. Remedial action: exclude `Item Code` from ML features.

### Key Decisions

- **Brand imbalance flagged as a critical observation, not just a low-severity issue:** Although the automated checker flags only `Item Code`, the Brand distribution — Brand_1 at 88% — was elevated to a critical finding in the conclusion because it could invalidate brand-level analyses if other brands are underrepresented due to data collection gaps rather than market reality.

### Issue Summary

| Column | Issue | Severity |
|--------|-------|----------|
| `Item Code` | High cardinality ratio — likely an identifier | Low |
| `Brand` | Severe concentration — Brand_1 = 88% | Critical observation |

### Notes / Additional Context

- Dataset is fully complete with zero missing values — excellent data quality for a dimension table.
- `Item Code` uniqueness (50 unique values for 50 rows) confirms it as a valid primary key.
- Priority action: confirm whether Brand_2 through Brand_6 are fully represented or whether additional product lines are missing from this extract.

---

## Dataset 3 — Region Mapping.csv

**Source:** `data/input/raw/Region Mapping.csv`
**Size:** 257 rows × 4 columns

### Working Assumptions

- `TerritoryID` is a unique geographic identifier and matches the `TerritoryID` foreign key in `invoice_level_sales.csv`.
- The named geographic levels (Region, District, Province) follow a strict hierarchy: Province → Region → District.
- Distribution imbalances at the District level are assumed to reflect genuine geographic variation rather than data gaps.

### Workflow Structure

1. Load CSV and confirm shape (257 × 4).
2. Profile dtypes — `TerritoryID` is `int64`; `Region`, `District`, `Province` are `str`.
3. Null analysis — zero nulls across all columns.
4. Categorical distributions for `Region` (12 unique), `District` (24 unique), `Province` (9 unique).
5. Automated DQ issue detection — 1 low-severity issue: `TerritoryID` flagged as high-cardinality ratio.
6. Remedial action: exclude `TerritoryID` from ML features; use only for joins.

### Key Decisions

- **TerritoryID treated as a join key, not a feature:** Its 1:1 cardinality ratio (257 unique values for 257 rows) confirms it is a primary key. This is the expected foreign key linking back to `invoice_level_sales.csv`.
- **Province chosen as primary aggregation level:** With only 9 distinct values and Province 3 accounting for 33.1% of coverage, Province offers the best balance between granularity and stability for geographic segmentation before more granular District-level analysis.

### Issue Summary

| Column | Issue | Severity |
|--------|-------|----------|
| `TerritoryID` | High cardinality ratio — primary key, not a feature | Low |

### Notes / Additional Context

- Dataset is fully complete with zero missing values.
- `Region 5` (24.1%) and `Region 6` (22.6%) together account for nearly half of all territory records — confirm this reflects expected geographic footprint.
- `Province 3` (33.1%) is significantly larger than other provinces; verify it is not an artifact of how territories were assigned.
- After joining with the sales dataset, validate that all `TerritoryID` values in `invoice_level_sales.csv` have a matching row in this mapping table — an unmatched territory ID would result in silent null regions in downstream aggregations.

---

## Cross-Dataset Notes

- **Join validation is a required next step.** The `TerritoryID` in `invoice_level_sales.csv` must be verified to fully overlap with the `Region Mapping` table. Similarly, `ItemCode` in the sales data should be validated against `Item Code` in the product mapping (note the spacing difference in column names, which may cause silent join failures).
- **Column name hygiene:** `DocumnetNumber` (typo), trailing spaces in product and region column names (e.g., `Product Category `, `District `), and the spacing difference in `ItemCode` vs `Item Code` should all be standardised during ingestion.
- **No High-severity issues** were found across any of the three datasets, indicating the raw data is broadly usable. The most material risks are the `PaymentTerm` nulls in sales and the Brand concentration in the product mapping.
