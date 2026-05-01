# Intermediate Tables — Comparison & Differences

All five tables live in `data/Intermediate/` and are produced by `pipelines/3_eda/eda_data_creation.py`. Each answers a different analytical question at a different grain.

---

## At a Glance

| Table | Primary Key | Grain | Zero-Filled? | Est. Rows | Built From | Used By |
|-------|-------------|-------|:---:|-----------|------------|---------|
| `base_sales_enriched` | (document_number, item_code) | Transaction line | No | ~6.8M | sales + product + region | Ad-hoc queries, all modules |
| `outlet_sku_monthly_demand` | (outlet_id, item_code, year_month) | Outlet × SKU × Month | Yes | ~2.5M+ | base_sales_enriched | Forecasting model (Module 2, 3) |
| `outlet_monthly_activity` | (outlet_id, year_month) | Outlet × Month | Yes | ~840K+ | base_sales_enriched | Outlet feature engineering (Module 5) |
| `monthly_territory_demand` | (year_month, territory_id) | Territory × Month | Yes | ~21K | outlet_sku_monthly_demand | Geographic analysis (Module 4) |
| `outlet_features` | outlet_id | Outlet (one row) | N/A | ~N outlets | outlet_monthly_activity | Clustering (Module 6) |

---

## Key Conceptual Differences

### 1. Grain (what one row represents)

The tables exist at progressively more aggregated grains:

```
base_sales_enriched         → one row per invoice line item (raw)
    ↓ aggregate + zero-fill
outlet_sku_monthly_demand   → one row per outlet × SKU × month
    ↓ drop SKU, aggregate
outlet_monthly_activity     → one row per outlet × month
    ↓ aggregate territories
monthly_territory_demand    → one row per territory × month
    ↓ collapse to one row
outlet_features             → one row per outlet (static feature snapshot)
```

### 2. Zero-filling

`base_sales_enriched` is a **raw fact table** — it only contains rows where a transaction happened. The other four tables are **exhaustive grids** built by cross-joining a date spine with an entity spine, so every combination of (entity, month) exists even if there was no activity that month. This is critical for time series models, which cannot have implicit gaps.

| Table | Has rows for inactive periods? |
|-------|-------------------------------|
| `base_sales_enriched` | No — sparse, event-only |
| `outlet_sku_monthly_demand` | Yes — zero-filled |
| `outlet_monthly_activity` | Yes — zero-filled |
| `monthly_territory_demand` | Yes — zero-filled (uses all 257 territories from `region.parquet`, including ones with zero sales history) |
| `outlet_features` | N/A — one static row per outlet; `is_active = False` marks churned outlets |

### 3. What metrics each table carries

| Metric | base_sales | outlet_sku_demand | outlet_activity | territory_demand | outlet_features |
|--------|:---:|:---:|:---:|:---:|:---:|
| Transaction-level detail (document_number, date) | ✓ | — | — | — | — |
| Net vs. gross vs. return split | ✓ | ✓ | ✓ | ✓ | — |
| n_unique_skus / n_unique_categories | — | — | ✓ | — | ✓ (max over window) |
| n_outlets_active | — | — | — | ✓ | — |
| Loyalty, recency, momentum, return_rate | — | — | — | — | ✓ |
| is_active flag | — | — | — | — | ✓ |
| primary_payment_term | — | — | ✓ | — | pct_cash_txn |

### 4. Time dimension

| Table | Time column | Scope |
|-------|-------------|-------|
| `base_sales_enriched` | `document_date` (date) + `year_month` (str) | Only months with transactions |
| `outlet_sku_monthly_demand` | `year_month` | Full date range, every month |
| `outlet_monthly_activity` | `year_month` | Full date range, every month |
| `monthly_territory_demand` | `year_month` | Full date range, every month |
| `outlet_features` | None (static) | Derived from last 12 months of activity |

### 5. Entity scope

| Table | Which outlets / territories are included? |
|-------|------------------------------------------|
| `base_sales_enriched` | Only outlets/territories that appear in sales data |
| `outlet_sku_monthly_demand` | Only outlet–SKU pairs with at least one invoice (active pairs) |
| `outlet_monthly_activity` | All unique outlets ever seen in sales |
| `monthly_territory_demand` | All 257 territories from `region.parquet` — including those with zero sales history |
| `outlet_features` | All unique outlets; `is_active = False` for those with zero activity in the last 12 months |

---

## When to Use Which Table

| Question | Use |
|----------|-----|
| What did outlet X buy on a specific date? | `base_sales_enriched` |
| How many units of SKU Y did outlet X buy in March? (including zero months) | `outlet_sku_monthly_demand` |
| How active was outlet X in a given month? (SKU-agnostic) | `outlet_monthly_activity` |
| What was total territory demand in a given month? | `monthly_territory_demand` |
| What behavioural profile does outlet X have for clustering? | `outlet_features` |
| National or territory-level trend / seasonality analysis | `outlet_sku_monthly_demand` (aggregate up) or `monthly_territory_demand` |
