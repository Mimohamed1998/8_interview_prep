# [Pipeline 9] Cohort Evaluation — Per-Item and Per-Outlet-Cluster WAPE/MAPE

**Date:** 2026-05-02  
**Pipeline:** Pipeline 9 — Breaks down forecast accuracy by item and by outlet cluster cohort, comparing raw vs. buffered forecasts  
**Output file:** `docs/17_cohort_evaluation.md`

---

## Overview

The cohort evaluation pipeline disaggregates model performance across two independent dimensions: individual SKU (`item_code`) and outlet cluster (`cluster_definition`). It reads the buffered predictions parquet produced by Pipeline 8, joins dimension metadata from the intermediate layer, and outputs two CSV files containing WAPE, MAPE, total volume, and absolute error metrics for both raw and buffered forecasts. The evaluation is scoped to the held-out period `2019-01 → 2019-10`.

---

## Working Assumptions

- Evaluation is performed exclusively on the `modeling.eval_start` → `modeling.eval_end` window (`2019-01 → 2019-10`), matching the train/eval split used during model development.
- Item demand class (`Continuous`, `Intermittent`, `Lumpy`) is sourced from `data/Intermediate/item_classification.parquet` and treated as fixed metadata.
- Outlet cluster membership (`Power`, `High-Value Active`, `Low-Value Sporadic`) is sourced from `data/Intermediate/outlet_cluster_definitions.parquet`. Churned outlets are absent from the buffered predictions (they were not scored at inference) so they do not appear in the evaluation output.
- MAPE is computed only over rows where `actual_qty > 0` to avoid division-by-zero for zero-demand periods — this is especially relevant for Lumpy and Intermittent demand classes.
- WAPE uses the full row set (including zero-actual rows) so its denominator reflects true total demand volume for the cohort.
- Both item and cluster evaluations are independent — items are not weighted by cluster, and clusters are not broken down by item in the standard outputs.

---

## Workflow Structure

1. Load `data/bu_raw_output/inference_parquet/predictions_buffered.parquet` (output of Pipeline 8).
2. Load dimension metadata:
   - `data/Intermediate/item_classification.parquet` → `item_code`, `demand_class`
   - `data/Intermediate/outlet_cluster_definitions.parquet` → `outlet_id`, `cluster_definition`
3. Filter both evaluation views to the eval window (`2019-01 → 2019-10`).
4. **Per-item evaluation:** group by `item_code`, apply `_eval_group()` to compute all metrics, left-join `demand_class`, sort by `wape_raw` descending.
5. **Per-outlet-cluster evaluation:** group by `cluster_definition`, apply `_eval_group()`, separately compute `n_outlets` (distinct outlet count per cluster), merge into result.
6. Write `eval_by_item.csv` (50 rows — one per SKU) to `data/bu_raw_output/inference_parquet/`.
7. Write `eval_by_outlet_cluster.csv` (3 rows — one per active cluster) to `data/bu_raw_output/inference_parquet/`.
8. Print formatted evaluation tables to stdout.

---

## Key Decisions

- **Two separate output files over one wide table:** Joining item and cluster dimensions into a single table would require a 50 × 3 cross-product with repeated volume figures. Keeping them separate preserves clarity and makes each file directly usable for reporting.
- **Sort per-item output by `wape_raw` descending:** Puts the worst-performing SKUs at the top, making triage faster without needing to sort in Excel or downstream tools.
- **`n_outlets` computed separately from `_eval_group`:** The generic `_eval_group` function operates on any groupby, so it can't count distinct outlets. A second `groupby → nunique` pass populates this column, keeping `_eval_group` reusable for any future cohort dimension.
- **`include_groups=False` in `apply`:** Prevents the groupby key column from being included in the group DataFrame passed to `_eval_group`, avoiding accidental inclusion in metric computations under newer pandas versions.
- **Left join for cluster and item metadata:** Ensures rows are not silently dropped if a SKU or outlet has no classification record — they appear with `NaN` in the dimension column, which makes data gaps visible rather than hidden.

---

## Notes / Additional Context

- **Run order:** Requires `pipelines/8_buffer/buffer_pipeline.py` to have run first (reads `predictions_buffered.parquet`).
- **Src module:** `src/model_prediction_pipelines/evaluation.py`
- **Pipeline entry point:** `python pipelines/9_evaluation/evaluation_pipeline.py`

### Per-Outlet-Cluster Results (eval window 2019-01 → 2019-10)

| Cluster | Outlets | Total Actual | WAPE Raw | MAPE Raw | WAPE Buffered | MAPE Buffered |
|---|---:|---:|:---:|:---:|:---:|:---:|
| Low-Value Sporadic | 32,430 | 1,377,941 | 2.667 | 0.834 | 2.383 | 0.896 |
| High-Value Active | 27,115 | 7,583,577 | 2.136 | 0.823 | 2.079 | 0.922 |
| Power | 5,247 | 27,113,272 | 1.466 | 0.854 | 1.622 | 0.977 |

**Interpretation:** Low-Value Sporadic has the highest raw WAPE (2.67) but shows the greatest benefit from the buffer (−0.28). Power outlets have the best raw WAPE (1.47) but the buffer marginally increases it (+0.16), suggesting erratic within-period demand patterns that cause the rolling bias estimate to overcorrect.

### Per-Item Results — Worst Performers by WAPE Raw

| Item | Demand Class | WAPE Raw | WAPE Buffered |
|---|---|:---:|:---:|
| gf8022002 | Lumpy | 12.649 | 9.567 |
| gf8031016 | Lumpy | 5.127 | 4.777 |
| gf4001604 | Lumpy | 3.811 | 3.132 |
| pf0013041 | Lumpy | 1.771 | 2.027 |

Lumpy-class items dominate poor accuracy — expected given their zero-inflated, high-variance demand structure. The buffer helps 3 of the 4 worst performers; `pf0013041` is a notable exception where the buffer overcorrects (likely due to a structural demand shift that makes recent errors a poor predictor).

Full 50-item table: `data/bu_raw_output/inference_parquet/eval_by_item.csv`

- **Follows:** `docs/16_buffer_mechanism.md`

---

## Per-Cell Cluster Results (eval window 2019-01 → 2019-10)

> Over-WAPE and Under-WAPE share the same denominator (`sum(actual)` for the full cell) so they are additive components of WAPE.  
> MAPE excludes zero-actual rows. All values rounded to 4 d.p.

### Raw Forecast

| Cell Cluster | MAPE | Over-WAPE | Under-WAPE | WAPE |
|---|:---:|:---:|:---:|:---:|
| cell_0_power_continuous | 0.7290 | 0.7268 | 0.7121 | 1.4389 |
| cell_1_power_intermittent | 0.8508 | 0.7417 | 0.7117 | 1.4534 |
| cell_2_power_lumpy | 1.0969 | 0.7550 | 0.8081 | 1.5631 |
| cell_3_high-value_active_continuous | 0.6985 | 0.8624 | 0.7439 | 1.6063 |
| cell_4_high-value_active_intermittent | 0.7863 | 1.2344 | 0.8198 | 2.0542 |
| cell_5_high-value_active_lumpy | 1.9177 | 7.6037 | 0.6581 | 8.2617 |
| cell_6_low-value_sporadic_continuous | 0.7672 | 1.2101 | 0.7919 | 2.0019 |
| cell_7_low-value_sporadic_intermittent | 0.8782 | 2.2399 | 0.8866 | 3.1265 |
| cell_8_low-value_sporadic_lumpy | 1.2230 | 13.9701 | 0.8946 | 14.8647 |

### Buffered Forecast

| Cell Cluster | MAPE | Over-WAPE | Under-WAPE | WAPE |
|---|:---:|:---:|:---:|:---:|
| cell_0_power_continuous | 0.9111 | 0.8916 | 0.7083 | 1.6000 |
| cell_1_power_intermittent | 0.9672 | 0.8764 | 0.7221 | 1.5985 |
| cell_2_power_lumpy | 1.1648 | 0.9871 | 0.7997 | 1.7869 |
| cell_3_high-value_active_continuous | 0.8584 | 0.9450 | 0.7592 | 1.7043 |
| cell_4_high-value_active_intermittent | 0.8873 | 1.1724 | 0.8358 | 2.0083 |
| cell_5_high-value_active_lumpy | 1.6440 | 5.9843 | 0.6321 | 6.6164 |
| cell_6_low-value_sporadic_continuous | 0.8462 | 1.1233 | 0.7940 | 1.9172 |
| cell_7_low-value_sporadic_intermittent | 0.9374 | 1.8082 | 0.8924 | 2.7006 |
| cell_8_low-value_sporadic_lumpy | 1.0828 | 10.2226 | 0.8149 | 11.0375 |

**Key observations:**
- `cell_8_low-value_sporadic_lumpy` and `cell_5_high-value_active_lumpy` have extreme Over-WAPE (13.97 and 7.60 raw) — the model massively over-forecasts these cells. The buffer significantly reduces Over-WAPE in both (→10.22 and →5.98).
- Under-WAPE is consistently low (0.65–0.90) across all cells, meaning under-forecasting is minor compared to over-forecasting.
- Power cells (0–2) have the most balanced Over/Under-WAPE and lowest overall WAPE, confirming the model is best calibrated there.
- Full output: `data/bu_raw_output/inference_parquet/eval_by_cell_cluster.csv`
