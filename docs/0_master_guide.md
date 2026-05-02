# Master Guide — How to Read This Codebase

**Date:** 2026-05-02
**Author:** Mohamed Inas
**Purpose:** Entry point for understanding the project structure, documentation conventions, and end-to-end workflow.

---

## 1. What This Project Does

This project builds a **monthly demand forecasting system** for an FMCG distribution business. Given historical invoice-level sales data, it produces per-outlet, per-SKU quantity forecasts for the next month. The system handles three distinct demand patterns (Continuous, Intermittent, Lumpy) across three outlet segments (Power, High-Value Active, Low-Value Sporadic), yielding a **3×3 grid of nine XGBoost models**.

The end product is a `predictions_buffered.parquet` file containing corrected monthly forecasts for all active outlet × SKU combinations, plus a cohort-level evaluation report.

---

## 2. Reading Order for the Docs

Each doc in `docs/` maps directly to a pipeline stage. Read them in numeric order — each doc references its predecessor. Start here and follow the chain.

| Doc | Title | What You Learn |
|:---:|-------|----------------|
| `1_dq_report.md` | Data Quality Report | Raw data health, null rates, outlier flags, join key risks |
| `2_raw_proceessing.md` | Raw Processing | How raw CSVs are cleaned, joined, and standardised |
| `3_intermediate_data_created.md` | Intermediate Data | What the 5 intermediate aggregation tables are and how they relate |
| `4_intermediate_tables_comparison.md` | Intermediate Tables Comparison | Column-by-column comparison of the aggregation outputs |
| `5_EDA_modeling_synthesis.md` | EDA & Modeling Synthesis | Key demand patterns discovered; inputs to the modeling strategy |
| `6_eda_ceo_briefing.md` | EDA CEO Briefing | Executive summary of demand structure and business implications |
| `7_item_classification_definitions.md` | Item Classification | How SKUs are labelled Continuous / Intermittent / Lumpy |
| `8_cluster_definitions.md` | Cluster Definitions | How outlets are segmented into Power / High-Value Active / Low-Value Sporadic |
| `9_modeling_strategy.md` | Modeling Strategy | The 3×3 model grid and why two-stage models exist for Lumpy cells |
| `10_modeling_features.md` | Modeling Features | The full feature set per demand class |
| `11_feature_merging_guide.md` | Feature Merging Guide | How features are joined to cell data before training |
| `12_feature_engineering_eda_summary.md` | Feature Engineering EDA | Exploratory validation of engineered features |
| `13_modeling_implementation.md` | Modeling Implementation | Training loop, hyperparameter search, cross-validation setup |
| `14_model_performance_io_instructions.md` | Model Performance & I/O | How trained models are serialised, loaded, and evaluated |
| `15_inference_pipeline.md` | Inference Pipeline | Batch scoring across all 9 cells → `predictions.parquet` |
| `16_buffer_mechanism.md` | Buffer Mechanism | Rolling 2-month error correction → `predictions_buffered.parquet` |
| `17_cohort_evaluation.md` | Cohort Evaluation | Segment-level WAPE/MAPE breakdown of final forecasts |

---

## 3. Pipeline Stages → Code Map

Each pipeline stage has an entry-point script under `pipelines/` and a supporting module under `src/`. The doc column tells you where the design intent is explained.

```
Stage                   Entry point                                 Src module                                  Doc
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
1  DQ Report            pipelines/1_dq_report/*.ipynb               src/common/dq.py                            docs/1_dq_report.md
2  Raw Processing       pipelines/2_raw_processing/main.py          src/utlits/raw_processing.py                docs/2_raw_proceessing.md
3  EDA Aggregations     pipelines/3_eda/create_01..05.py            src/common/data_utils.py                    docs/3_intermediate_data_created.md
4  Item Classification  pipelines/4_item_product_classification/    src/item_classification/item_classification.py  docs/7_item_classification_definitions.md
5  Feature Engineering  pipelines/5_feature_engineering/            src/feature_engineering/feature_engineering.py  docs/10_modeling_features.md
6  Modeling (9 cells)   pipelines/6_modeling/model_1..9.ipynb       src/modeling/                               docs/9_modeling_strategy.md, 13_modeling_implementation.md
7  Inference            pipelines/7_inference/inference_pipeline.py src/model_prediction_pipelines/model_prediction.py  docs/15_inference_pipeline.md
8  Buffer               pipelines/8_buffer/buffer_pipeline.py       src/model_prediction_pipelines/buffer.py    docs/16_buffer_mechanism.md
9  Evaluation           pipelines/9_evaluation/evaluation_pipeline.py  src/model_prediction_pipelines/evaluation.py  docs/17_cohort_evaluation.md
10 Export               pipelines/10_export_csv/export_pipeline.py  —                                           —
20 Monthly Inference    pipelines/20_monthly_pipelines/             —                                           —
```

### The `src/modeling/` Sub-modules

When reading a modeling notebook or the inference pipeline, these are the key src files:

| File | Purpose |
|------|---------|
| `data_loader.py` | Loads a cell parquet and merges features |
| `splitter.py` | Produces time-based train/test splits |
| `feature_selector.py` | Selects the right feature set per demand class |
| `search.py` | Hyperparameter search (cross-validation) |
| `regressor.py` | XGBoost regressor wrapper |
| `classifier.py` | XGBoost classifier wrapper (Lumpy Stage 1) |
| `two_stage.py` | Orchestrates Classifier → Regressor for Lumpy cells |
| `metrics.py` | WAPE, MAPE, MAE calculation |
| `model_io.py` | Save/load `.pkl` model files |

---

## 4. The 3×3 Modeling Grid at a Glance

The core design decision of this project — read `docs/9_modeling_strategy.md` for full rationale.

|  | **Continuous** | **Intermittent** | **Lumpy** |
|---|---|---|---|
| **Power Outlets** | XGBoost Regressor | XGBoost Regressor | XGBoost Regressor |
| **High-Value Active (Cluster 0)** | XGBoost Regressor | XGBoost Regressor | **2-Stage: Classifier + Regressor** |
| **Low-Value Sporadic (Cluster 1)** | XGBoost Regressor | XGBoost Regressor | **2-Stage: Classifier + Regressor** |

- **Single-stage cells (7):** Model files are `{model_name}.pkl`.
- **Two-stage cells (2):** Model files are `{model_name}_stage1_clf.pkl` + `{model_name}_stage2_reg.pkl`.
- The `lumpy` flag in the Cell Registry in `inference_pipeline.py` controls which path is taken.

---

## 5. Data Flow — Files in, Files out

```
data/input/raw/
  invoice_level_sales.csv          ← 6.8M rows, source transactions
  Product Mapping.csv              ← 50 SKUs, dimension table
  Region Mapping.csv               ← 257 territories, dimension table
       │
       ▼  pipelines/2_raw_processing/
data/input/processed/
  sales_enriched.parquet           ← cleaned, joined, date-parsed
       │
       ▼  pipelines/3_eda/create_01..05.py
data/Intermediate/
  base_sales_enriched.parquet
  outlet_sku_monthly_demand.parquet
  outlet_monthly_activity.parquet
  monthly_territory_demand.parquet
  outlet_features.parquet
  cell_0..8_*.parquet              ← 9 cell parquets (outlet×SKU×month grid)
       │
       ▼  pipelines/5_feature_engineering/ → pipelines/6_modeling/
data/output/models/
  model_0_power_continuous.pkl
  model_1_power_intermittent.pkl
  ... (7 single-stage)
  model_5_high-value_active_lumpy_stage1_clf.pkl
  model_5_high-value_active_lumpy_stage2_reg.pkl
  model_8_low-value_sporadic_lumpy_stage1_clf.pkl
  model_8_low-value_sporadic_lumpy_stage2_reg.pkl
       │
       ▼  pipelines/7_inference/
data/bu_raw_output/inference_parquet/
  predictions.parquet              ← 5,866,201 rows, raw scores
       │
       ▼  pipelines/8_buffer/
  predictions_buffered.parquet     ← bias-corrected, clipped ≥ 0
  buffer_metrics.csv               ← WAPE/MAPE before/after
       │
       ▼  pipelines/9_evaluation/ → pipelines/10_export_csv/
  [evaluation reports + final export]
```

---

## 6. Configuration

All pipeline parameters live in `conf/conf.yml`. You do not need to touch code to change windows or thresholds:

```yaml
modeling:
  train_start: "2015-01"
  train_end:   "2018-09"
  eval_start:  "2019-01"
  eval_end:    "2019-10"

inference:
  start: "2018-10"
  end:   "2019-12"
  cell_data_path: "data/Intermediate"
  model_path:     "data/output/models"
  output_path:    "data/bu_raw_output/inference_parquet"

buffer:
  n_months: 2
  classifier_threshold: 0.5
```

Config is loaded via `src/common/utils/config.py` and passed as `cfg` into every pipeline function.

---

## 7. Running the Full Pipeline (Correct Order)

```bash
# 1. DQ (exploratory, not required to re-run)
jupyter nbconvert --to notebook --execute pipelines/1_dq_report/*.ipynb

# 2. Raw processing
python pipelines/2_raw_processing/main.py

# 3. Intermediate aggregations (run in order 01→05)
python pipelines/3_eda/create_01_base_sales_enriched.py
python pipelines/3_eda/create_02_outlet_sku_monthly_demand.py
python pipelines/3_eda/create_03_outlet_monthly_activity.py
python pipelines/3_eda/create_04_monthly_territory_demand.py
python pipelines/3_eda/create_05_outlet_features.py

# 4. Item classification
python pipelines/4_item_product_classification/item_classification.py

# 5. Feature engineering
python pipelines/5_feature_engineering/feature_engineering.py

# 6. Train 9 models (can parallelise across cells)
jupyter nbconvert --to notebook --execute pipelines/6_modeling/model_1_power_continuous.ipynb
# ... repeat for model_2 through model_9

# 7. Inference
python pipelines/7_inference/inference_pipeline.py

# 8. Buffer correction
python pipelines/8_buffer/buffer_pipeline.py

# 9. Evaluation
python pipelines/9_evaluation/evaluation_pipeline.py

# 10. Export
python pipelines/10_export_csv/export_pipeline.py
```

---

## 8. Monthly Re-run (Production Cadence)

For recurring monthly scoring without re-training, use the `pipelines/20_monthly_pipelines/` shortcuts:

```bash
python pipelines/20_monthly_pipelines/0_create_item_monthly_data.py
jupyter nbconvert --to notebook --execute pipelines/20_monthly_pipelines/model_1_continuous_intermittent.ipynb
jupyter nbconvert --to notebook --execute pipelines/20_monthly_pipelines/model_2_lumpy.ipynb
```

These notebooks load the existing trained models and score the latest month of data only.

---

## 9. Testing

Four test notebooks in `test/` validate the outputs of the most critical stages:

| Notebook | What it checks |
|---------|---------------|
| `test_model_io_predictions.ipynb` | Models load correctly and produce non-null predictions |
| `test_model_3_hva_continuous.ipynb` | HVA Continuous model performance metrics |
| `test_inference_output.ipynb` | `predictions.parquet` shape, columns, row count, cell coverage |
| `eda_intermediate.ipynb` | Intermediate table shapes and join integrity |

Run these after any pipeline change to catch regressions before they reach the buffer stage.

---

## 10. Common Entry Points for New Readers

| Goal | Start here |
|------|------------|
| Understand the business problem | `docs/6_eda_ceo_briefing.md` |
| Understand why 9 models exist | `docs/9_modeling_strategy.md` |
| Understand how a SKU gets classified | `docs/7_item_classification_definitions.md` |
| Understand how outlets are segmented | `docs/8_cluster_definitions.md` |
| Understand the feature set | `docs/10_modeling_features.md` |
| Understand how raw forecasts are corrected | `docs/16_buffer_mechanism.md` |
| Run the pipeline end-to-end | Section 7 of this doc |
| Find a specific src function | Section 3 of this doc |
