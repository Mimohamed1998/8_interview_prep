# Inference Pipeline — Batch Demand Predictions

**Author:** Mohamed Inas  
**Created:** 2026-05-02  
**Depends on:** `docs/14_model_performance_io_instructions.md`  
**Pipeline:** `pipelines/7_inference/inference_pipeline.py`  
**Src module:** `src/model_prediction_pipelines/model_prediction.py`  
**Output:** `data/bu_raw_output/inference_parquet/predictions.parquet`  
**Test notebook:** `test/test_inference_output.ipynb`

---

## 1. Purpose

Scores all nine trained XGBoost models over a configurable inference window and produces a single consolidated predictions parquet. The pipeline handles both single-stage regressors (7 cells) and two-stage classifier + regressor models (2 cells) transparently.

---

## 2. Inference Window

Configured in `conf/conf.yml` under the `inference` key:

```yaml
inference:
  start: "2018-10"
  end:   "2019-12"
  cell_data_path: "data/Intermediate"
  model_path:     "data/output/models"
  output_path:    "data/bu_raw_output/inference_parquet"
```

The window `2018-10 → 2019-12` covers 3 months of pre-eval history plus the full evaluation period, giving downstream consumers both in-sample trailing context and the out-of-sample forecast horizon.

---

## 3. Pipeline Architecture

```
conf/conf.yml
     │
     ▼
inference_pipeline.py::main()
     │
     ├── build_predictions(cfg)
     │        │
     │        └── src/model_prediction_pipelines/model_prediction.py::run_inference(cfg)
     │                 │
     │                 │  for each of 9 CELL_REGISTRY entries:
     │                 ├── filter_inference_window(df, start, end)
     │                 └── predict_cell(df_infer, model_path, cell_meta, mod_cfg)
     │                          ├── single-stage: load_model() → reg.predict()
     │                          └── two-stage:    load_model() × 2 → _predict_two_stage()
     │
     └── write_parquet(predictions, output_path/predictions.parquet)
```

**Rule:** All file writes happen exclusively in `main()`. The src functions return DataFrames only.

---

## 4. Cell Registry

The pipeline iterates a static registry of all 9 grid cells. The `lumpy` flag selects single-stage vs two-stage inference:

| Cell | Parquet | Model prefix | Stage |
|:----:|---------|-------------|:-----:|
| 0 | `cell_0_power_continuous.parquet` | `model_0_power_continuous` | Single |
| 1 | `cell_1_power_intermittent.parquet` | `model_1_power_intermittent` | Single |
| 2 | `cell_2_power_lumpy.parquet` | `model_2_power_lumpy` | Single |
| 3 | `cell_3_high-value_active_continuous.parquet` | `model_3_high-value_active_continuous` | Single |
| 4 | `cell_4_high-value_active_intermittent.parquet` | `model_4_high-value_active_intermittent` | Single |
| 5 | `cell_5_high-value_active_lumpy.parquet` | `model_5_high-value_active_lumpy` | Two-stage |
| 6 | `cell_6_low-value_sporadic_continuous.parquet` | `model_6_low-value_sporadic_continuous` | Single |
| 7 | `cell_7_low-value_sporadic_intermittent.parquet` | `model_7_low-value_sporadic_intermittent` | Single |
| 8 | `cell_8_low-value_sporadic_lumpy.parquet` | `model_8_low-value_sporadic_lumpy` | Two-stage |

Two-stage model files follow the pattern `{model_name}_stage1_clf.pkl` + `{model_name}_stage2_reg.pkl`.

---

## 5. Output Schema

`data/bu_raw_output/inference_parquet/predictions.parquet`

| Column | Type | Description |
|--------|------|-------------|
| `outlet_id` | str | Outlet identifier |
| `item_code` | str | SKU identifier |
| `year_month` | str | Period in `YYYY-MM` format |
| `predicted_qty` | float64 | Predicted raw sales quantity (clipped ≥ 0 for single-stage; may be negative for two-stage edge cases) |
| `cell_name` | str | Source grid cell, e.g. `cell_0_power_continuous` |

**Row count (current run):** 5,866,201 rows across 13 months (2018-10 → 2019-10).

---

## 6. Running the Pipeline

```bash
# From project root
python pipelines/7_inference/inference_pipeline.py
```

Expected output:
```
Wrote 5,866,201 rows → data/bu_raw_output/inference_parquet/predictions.parquet
```

---

## 7. Src Functions Reference

All inference logic lives in `src/model_prediction_pipelines/model_prediction.py`.

### `filter_inference_window(df, start, end)`
Filters a cell DataFrame to rows where `year_month` falls within `[start, end]` inclusive.

### `predict_cell(df_infer, model_path, cell_meta, mod_cfg)`
Loads model(s) for one grid cell, builds the feature matrix via `get_feature_columns()`, and returns a slim DataFrame with `outlet_id`, `item_code`, `year_month`, `predicted_qty`.

- Single-stage: loads one regressor, applies `np.clip(y_pred, 0, None)`.
- Two-stage: loads classifier + regressor, applies `_predict_two_stage()` using `classifier_threshold` from conf.

### `run_inference(cfg)`
Iterates all 9 entries in `CELL_REGISTRY`, calls `filter_inference_window` and `predict_cell` per cell, appends `cell_name`, and returns the concatenated DataFrame.

---

## 8. Verifying the Output

Open `test/test_inference_output.ipynb` and run all cells. It checks:

1. The parquet path resolves and the file exists.
2. Shape, columns, and `year_month` range are as expected.
3. All 9 `cell_name` values are present.
4. A 10-row sample and `predicted_qty` descriptive stats are displayed.

---

*Prepared: 2026-05-02. Follows `docs/14_model_performance_io_instructions.md`.*
