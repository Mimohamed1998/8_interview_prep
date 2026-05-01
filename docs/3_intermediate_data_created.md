# Intermediate Data Creation Documentation

## Overview

This document describes the intermediate data creation process for the EDA pipeline (Module 0). The pipeline reads processed parquet files from `data/input/processed/` and creates five intermediate datasets saved to `data/Intermediate/` in parquet format.

## Pipeline Execution

Run the pipeline using:

```bash
python pipelines/3_eda/eda_data_creation.py
```

## Input Datasets

- `sales.parquet`: Processed sales transactions
- `product.parquet`: Processed product mapping
- `region.parquet`: Processed region mapping

## Output Datasets

### 1. base_sales_enriched.parquet

**Purpose**: Single enriched fact table combining all source tables for ad-hoc analysis.

**Primary Key**: (document_number, item_code)

**Construction**:
- Load sales.parquet
- Parse document_date to datetime
- Derive year_month as YYYY-MM string
- Left join with product.parquet on item_code
- Left join with region.parquet on territory_id

**Schema**:
- document_number, document_date, year_month, outlet_id, territory_id, item_code, route_id, payment_term, document_type, net_sales, quantity
- product_category, product_line, brand
- region, district, province

### 2. outlet_sku_monthly_demand.parquet

**Purpose**: Fully populated monthly demand time series for every active outlet-SKU combination.

**Primary Key**: (outlet_id, item_code, year_month)

**Construction**:
- Build date spine from min to max document_date
- Build active outlet-SKU pairs (where document_type == 'invoice')
- Cross join date and active pair spines
- Left join aggregated monthly demand onto the grid
- Fill nulls with 0
- Add product and region dimensions

**Schema**:
- outlet_id, item_code, year_month, territory_id, product_category, product_line, brand, region, district, province
- net_quantity, net_sales, gross_quantity, gross_sales, return_quantity, return_sales, n_invoices, n_returns

### 3. outlet_monthly_activity.parquet

**Purpose**: Fully populated monthly activity record for every outlet.

**Primary Key**: (outlet_id, year_month)

**Construction**:
- Build date spine
- Build outlet spine from all unique outlet_id
- Cross join date and outlet spines
- Left join aggregated monthly activity
- Fill nulls appropriately
- Add region dimensions

**Schema**:
- outlet_id, year_month, territory_id, region, district, province
- n_invoices, gross_quantity, gross_sales, n_returns, return_quantity, return_sales, n_unique_skus, n_unique_categories, primary_payment_term

### 4. monthly_territory_demand.parquet

**Purpose**: Monthly demand aggregated to territory level.

**Primary Key**: (year_month, territory_id)

**Construction**:
- Build date and territory spines
- Cross join
- Aggregate outlet_sku_monthly_demand to territory-month level
- Left join onto grid
- Add region dimensions

**Schema**:
- year_month, territory_id, region, district, province
- net_quantity, net_sales, gross_quantity, gross_sales, return_quantity, return_sales, n_unique_skus

### 5. outlet_features.parquet

**Purpose**: One-row-per-outlet feature matrix for clustering.

**Primary Key**: outlet_id

**Construction**:
- Filter outlet_monthly_activity to last 12 months
- Aggregate features per outlet
- Add is_active flag
- Add region dimensions

**Schema**:
- outlet_id, territory_id, region, province, is_active
- total_net_sales, total_quantity, active_months, loyalty_ratio, avg_txn_per_active_month, avg_net_sales_per_txn, avg_qty_per_txn, n_unique_skus, n_unique_categories, return_rate, recency_months, momentum, pct_cash_txn

## Logging

The pipeline logs key steps including row counts and output paths. All logging follows the configuration in `conf/conf.yml`.

## Dependencies

- pandas
- src.common.utils.config
- src.common.data_utils
- src.utlits.raw_processing