# 2 — Raw Processing

**Date:** 2026-05-01
**Pipeline:** `pipelines/2_raw_processing/main.py`

---

## Overview

This pipeline reads the three raw CSV files from `data/input/raw/`, applies standardisation and
business-logic transformations, and writes the results as parquet files to `data/input/processed/`.
All configuration is driven from `conf/conf.yml` under the `raw_processing` key.

---

## Input Sources

| Dataset | File | Rows (approx.) | Columns |
|---------|------|----------------|---------|
| Sales | `invoice_level_sales.csv` | 6,799,893 | 12 |
| Product | `Product Mapping.csv` | 50 | 4 |
| Region | `Region Mapping.csv` | 257 | 4 |

### Raw Schemas

**Sales**

| Column | Raw dtype |
|--------|-----------|
| documentDate | str |
| DocumnetNumber | str |
| OutletID | object |
| TerritoryID | int64 |
| DocumentType | str |
| ItemCode | str |
| RouteID | str |
| PaymentTerm | str |
| IsDirectDistributor | str |
| NetSales | float64 |
| Quantity | int64 |
| Discount | float64 |

**Product**

| Column | Raw dtype |
|--------|-----------|
| Item Code | str |
| Product Category | str |
| Product line | str |
| Brand | str |

**Region**

| Column | Raw dtype |
|--------|-----------|
| TerritoryID | int64 |
| Region | str |
| District | str |
| Province | str |

---

## Processing Steps

### Applied to All Datasets

1. **Column name standardisation** (`standardize_column_names`)
   - Strip leading/trailing whitespace
   - Convert to lowercase
   - Replace whitespace and hyphens with `_`
   - Remove all remaining non-alphanumeric characters (except `_`)

2. **Categorical value standardisation** (`standardize_categorical_values`)
   - Applied to every `object`-dtype column
   - Same cleaning rules as column names: lowercase, spaces → `_`, strip special characters

### Sales — Additional Steps

3. **Type casts** — `outlet_id` and `territory_id` cast from their raw types to `str`
4. **Drop column** — `is_direct_distributor` removed (business requirement)
5. **Returns business rule** — Where `document_type == 'return'`:
   - `net_sales` is already stored as a negative value (no change)
   - `quantity` is multiplied by `−1` to align sign with net_sales

### Region — Additional Steps

3. **Type cast** — `territory_id` cast from `int64` to `str` for consistent joining

### Product — No additional steps

---

## Output Schema

**`data/input/processed/sales.parquet`**

| Column | dtype |
|--------|-------|
| document_date | str |
| documnet_number | str |
| outlet_id | str |
| territory_id | str |
| document_type | str |
| item_code | str |
| route_id | str |
| payment_term | str |
| net_sales | float64 |
| quantity | int64 |
| discount | float64 |

> `is_direct_distributor` is dropped.
> For rows where `document_type == 'return'`, `quantity` is negative.

**`data/input/processed/product.parquet`**

| Column | dtype |
|--------|-------|
| item_code | str |
| product_category | str |
| product_line | str |
| brand | str |

**`data/input/processed/region.parquet`**

| Column | dtype |
|--------|-------|
| territory_id | str |
| region | str |
| district | str |
| province | str |

---

## Configuration (`conf/conf.yml`)

```yaml
raw_processing:
  files:
    sales:   invoice_level_sales.csv
    product: Product Mapping.csv
    region:  Region Mapping.csv
  sales:
    drop_columns:         [is_direct_distributor]
    return_document_type: return
    id_columns_to_str:    [outlet_id, territory_id]
  region:
    id_columns_to_str: [territory_id]
```

---

## How to Run

From the project root:

```bash
python pipelines/2_raw_processing/main.py
```

The pipeline logs each read, transform, and write step at `INFO` level.

Verify output:

```bash
ls data/input/processed/
# sales.parquet  product.parquet  region.parquet

python -c "
import pandas as pd
df = pd.read_parquet('data/input/processed/sales.parquet')
print(df.dtypes)
print(df[df.document_type == 'return'][['document_type','net_sales','quantity']].head())
"
```
