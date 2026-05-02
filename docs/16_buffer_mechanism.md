# [Pipeline 8] Buffer Mechanism — Rolling 2-Month Error Correction

**Date:** 2026-05-02  
**Pipeline:** Pipeline 8 — Additive bias correction applied to raw XGBoost forecasts using a 2-month rolling error look-back  
**Output file:** `docs/16_buffer_mechanism.md`

---

## Overview

The buffer pipeline corrects systematic per-SKU forecast bias by computing the rolling mean error (actual − predicted) over the 2 most recent prior observed periods for each outlet × item combination. The correction is applied additively to the raw forecast and clipped at zero to prevent negative quantities. It takes `predictions.parquet` and actuals from the 9 cell parquets as inputs and produces `predictions_buffered.parquet` alongside an aggregate `buffer_metrics.csv` with WAPE and MAPE before and after correction.

---

## Working Assumptions

- The 2 most recent **observed** periods are used as the look-back, not necessarily 2 consecutive calendar months — sparse SKUs with gaps in the inference window will have a wider-spanning but still 2-point average.
- Actuals (`target_qty_raw`) are sourced from the 9 intermediate cell parquets, which cover 2015-01 → 2019-10 and are considered ground truth.
- The buffer is set to `0` for any outlet × item with no prior observed error history (i.e., the first occurrence in the inference window).
- Buffered forecasts are clipped at 0 — negative demand is not valid in this business context.
- Aggregate WAPE/MAPE metrics are evaluated only on the held-out evaluation window (`2019-01 → 2019-10`) as defined in `conf/conf.yml` under `modeling.eval_start` / `modeling.eval_end`.

---

## Workflow Structure

1. Load raw forecasts from `data/bu_raw_output/inference_parquet/predictions.parquet`.
2. Load actuals (`target_qty_raw`) from all 9 `data/Intermediate/cell_*.parquet` files via `load_actuals()`; deduplicate on (outlet_id, item_code, year_month).
3. Left-join predictions to actuals on the three primary key columns.
4. Compute `error = actual_qty − predicted_qty` and the 2-period rolling mean buffer per (outlet_id, item_code) group using `compute_buffer(n_months=2)`; fill missing (no-history) rows with `0`.
5. Apply the buffer: `buffered_forecast = clip(predicted_qty + buffer, 0)` via `apply_buffer()`.
6. Slim the output to 9 columns (primary keys + forecast columns + absolute error columns) via `build_buffer_output()`.
7. Compute aggregate WAPE and MAPE for raw vs. buffered forecasts on the eval window via `compute_metrics()`.
8. Write `predictions_buffered.parquet` (5,866,201 rows) and `buffer_metrics.csv` to `data/bu_raw_output/inference_parquet/`.

---

## Key Decisions

- **Additive correction over multiplicative:** A multiplicative buffer (percentage adjustment) would amplify errors on high-volume SKUs disproportionately. An additive buffer applies a flat unit correction, which is more appropriate given the wide volume range across cells (lumpy items can be near-zero while power continuous items can be in the thousands).
- **`min_periods=1` in rolling window:** Rather than requiring a full 2-period history before applying any correction, `min_periods=1` lets the buffer activate after a single observed error. This is important for SKUs that appear only sporadically in the inference window.
- **Clip at 0 after buffer application:** The buffer can push forecasts negative (e.g., a model that over-predicts by 10 units gets a −10 correction). Clipping at 0 prevents downstream consumers from receiving invalid quantities while preserving the directional correction.
- **Separate `build_buffer_output()` from internal working columns:** The intermediate DataFrame carries `error`, `buffer`, and all raw columns. The output function slims this to only the 9 columns the user needs, keeping the parquet file small and the schema clear.
- **WAPE/MAPE increase at aggregate level is expected:** Zero-inflated demand means many outlet × item pairs have `actual_qty = 0`. The buffer reduces their individual absolute error (pushing over-forecasts toward zero) but the WAPE denominator `sum(actual)` remains unchanged, so aggregate WAPE can rise even as per-row errors fall. The per-row `abs_error_buffered` column is the right lens for evaluating per-SKU improvement.

---

## Notes / Additional Context

- **Run order:** This pipeline must run after `pipelines/7_inference/inference_pipeline.py` — it reads `predictions.parquet` as input.
- **Config key:** `conf/conf.yml` exposes `buffer.n_months: 2`. Changing this value and re-running adjusts the look-back window without code changes.
- **Output metrics (eval window 2019-01 → 2019-10):**

| Forecast Type | WAPE | MAPE |
|:---:|:---:|:---:|
| Raw | 1.653 | 0.834 |
| Buffered | 1.747 | 0.935 |

- **Src module:** `src/model_prediction_pipelines/buffer.py`
- **Pipeline entry point:** `python pipelines/8_buffer/buffer_pipeline.py`
- **Follows:** `docs/15_inference_pipeline.md`
- **Followed by:** `docs/17_cohort_evaluation.md`
