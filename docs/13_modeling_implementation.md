# Modeling Implementation Plan — Demand Forecasting Pipeline

**Author:** Mohamed Inas  
**Created:** 2026-05-02  
**Implements:** `docs/9_modeling_strategy.md`  
**Data source:** `data/Intermediate/full_reduced_modeling_matrix.parquet` (57 cols × 23,442,722 rows)  
**Depends on:** `docs/12_feature_engineering_eda_summary.md`

---

## Overview

Nine XGBoost models covering the 3×3 grid of (outlet segment) × (demand class). Seven are single-stage regressors; two are two-stage classifier+regressor for lumpy demand in non-Power clusters.

```
                     Continuous          Intermittent        Lumpy
Power                Model 1 (R)         Model 2 (R)         Model 3 (R)
High-Value Active    Model 4 (R)         Model 5 (R)         Model 6 (C+R)
Low-Value Sporadic   Model 7 (R)         Model 8 (R)         Model 9 (C+R)

R = XGBoost Regressor     C+R = XGBoost Classifier (Stage 1) + Regressor (Stage 2)
```

---

## 1. Data Source

Load from the convenience file produced by `pipelines/5_feature_engineering/feature_engineering_eda.ipynb`:

```
data/Intermediate/full_reduced_modeling_matrix.parquet
  23,442,722 rows × 57 columns
```

**Column categories in the 57-column matrix:**

| Category | Columns | Action |
|---|---|---|
| Identifiers | `outlet_id`, `item_code`, `year_month` | Drop before training |
| Geo/admin (forbidden) | `territory_id`, `region`, `district`, `province` | Drop before training |
| Product admin (forbidden) | `product_category`, `product_line`, `brand` | Drop before training |
| Segment strings (for filtering only) | `cluster_definition`, `demand_class` | Filter then drop |
| Target leakage | `target_qty_raw`, `target_qty_log1p`, `target_is_nonzero`, `target_log1p_net_sales` | Keep only the active target; drop all others |
| Numeric features (54) | All remaining columns | Use as model input |

---

## 2. Conf Additions Required

Add the following block to `conf/conf.yml` under the existing sections:

```yaml
modeling:
  # Time-based split — hard boundary, never random
  train_start: "2015-01"
  train_end:   "2018-12"
  eval_start:  "2019-01"
  eval_end:    "2019-12"

  # Target column names
  target_regressor:  "target_qty_log1p"
  target_classifier: "target_is_nonzero"

  # MLflow
  mlflow_experiment:   "demand_forecasting"
  mlflow_tracking_uri: "mlruns"

  # RandomizedSearchCV
  n_iter:    10
  cv_splits: 3
  random_state: 42

  # Two-stage decision threshold (Stage 1 classifier)
  classifier_threshold: 0.5

  # Output directory for saved .pkl models
  model_output_path: "data/output/models"

  # Columns to drop from feature matrix before training
  # (listed explicitly so notebooks remain source-of-truth free of hard codes)
  drop_columns:
    identifiers:      ["outlet_id", "item_code", "year_month"]
    geo_admin:        ["territory_id", "region", "district", "province"]
    product_admin:    ["product_category", "product_line", "brand"]
    segment_strings:  ["cluster_definition", "demand_class"]
    target_leakage:   ["target_qty_raw", "target_qty_log1p", "target_is_nonzero", "target_log1p_net_sales"]

  # XGBoost hyperparameter search space (used by RandomizedSearchCV)
  xgb_param_grid:
    n_estimators:      [100, 200, 300, 500]
    max_depth:         [3, 4, 5, 6, 7]
    learning_rate:     [0.01, 0.05, 0.1, 0.2]
    subsample:         [0.6, 0.8, 1.0]
    colsample_bytree:  [0.6, 0.8, 1.0]
    min_child_weight:  [1, 3, 5]
    reg_alpha:         [0, 0.1, 0.5, 1.0]
    reg_lambda:        [0.5, 1.0, 2.0]
```

---

## 3. Data Leakage Policy

### Forbidden as input features
Any column whose value at time T encodes information about the target (net_quantity at T+2):

| Column | Why it leaks |
|---|---|
| `target_qty_raw` | IS the target (future quantity) |
| `target_qty_log1p` | log transform of target |
| `target_is_nonzero` | binary derived from target |
| `target_log1p_net_sales` | future net_sales |

### Safe current-period features
`net_sales`, `yoy_growth`, `price_per_unit`, all lag/rolling/zero-inflation features — these are all computed from history at or before time T. They are available at prediction time when forecasting T+2.

### Per-model target assignment

| Model type | Active target (y) | Remaining target columns |
|---|---|---|
| Regressor | `target_qty_log1p` | Drop all others |
| Stage-1 Classifier | `target_is_nonzero` | Drop all others |
| Stage-2 Regressor (rows where target_is_nonzero==1) | `target_qty_log1p` | Drop all others |

> **Important:** Drop `target_qty_raw` even for regressors; back-transform predictions using `np.expm1()` to get raw-unit predictions.

---

## 4. Time-Based Split

```
2015-01 ────────────────── 2018-12 | 2019-01 ──── 2019-12
        TRAINING (48 months)       |  EVALUATION (12 months)
```

- **No random shuffle.** Split is a hard date boundary on `year_month`.
- Training rows: `year_month <= "2018-12"`
- Eval rows:     `year_month >= "2019-01"`
- Within-training CV for hyperparameter search: `sklearn.model_selection.TimeSeriesSplit(n_splits=cv_splits)` with chronological folds — no data leakage across folds.
- Rows with null targets (last 2 rows per outlet-item series) are dropped before any split.

---

## 5. Evaluation Metrics

Both metrics are computed on back-transformed predictions (`np.expm1(y_pred_log)` vs `target_qty_raw`).

### MAPE
```
MAPE = mean(|actual - predicted| / (|actual| + ε)) × 100
ε = 1e-8  (stabiliser)
```
> MAPE is undefined when actual = 0. For Intermittent and Lumpy models, compute MAPE only over non-zero actuals and report the zero-demand fraction separately.

### WMAPE (primary metric for Power outlets)
```
WMAPE = sum(|actual - predicted|) / sum(actual + ε) × 100
```
WMAPE is robust to zero actuals and revenue-weights large orders naturally. Use this as the headline metric for model comparison.

Both are logged to MLflow alongside `MAE` and `RMSE` (on log scale) for completeness.

---

## 6. Source Module Layout — `src/modeling/`

```
src/modeling/
├── __init__.py
├── data_loader.py       load matrix, filter to grid cell, apply row-activity filter
├── feature_selector.py  return feature column list (drops forbidden columns, active target only)
├── splitter.py          time-based train/eval split on year_month
├── metrics.py           mape(), wmape() — both operate on raw (back-transformed) scale
├── search.py            randomized_grid_search() — wraps RandomizedSearchCV + mlflow logging
├── regressor.py         train_regressor() — single-stage XGBRegressor pipeline
├── classifier.py        train_classifier() — Stage-1 XGBClassifier with scale_pos_weight
├── two_stage.py         train_two_stage(), predict_two_stage() — orchestrate C+R pipeline
└── model_io.py          save_model(), load_model() — pickle serialisation
```

### Function signatures

```python
# data_loader.py
def load_cell(matrix_path, cluster_name, demand_class):
    """Load and filter the modeling matrix to a single grid cell.

    Args:
        matrix_path: Path to full_reduced_modeling_matrix.parquet.
        cluster_name: One of "Power", "High-Value Active", "Low-Value Sporadic".
        demand_class: One of "Continuous", "Intermittent", "Lumpy".

    Returns:
        pandas DataFrame filtered to the requested cell, null targets dropped.
    """

# feature_selector.py
def get_feature_columns(df, target_col, drop_cfg):
    """Return the feature column list for a given model, removing forbidden and leak columns.

    Args:
        df: Full cell DataFrame.
        target_col: The active target column to retain as y (all others in target group dropped).
        drop_cfg: dict from conf modeling.drop_columns.

    Returns:
        Tuple of (feature_cols: list[str], target_col: str).
    """

# splitter.py
def time_split(df, train_end, eval_start):
    """Split DataFrame into train and eval sets on year_month.

    Args:
        df: Cell DataFrame with year_month column.
        train_end: Last month of training window, e.g. "2018-12".
        eval_start: First month of eval window, e.g. "2019-01".

    Returns:
        Tuple of (df_train, df_eval).
    """

# metrics.py
def mape(y_true, y_pred, eps=1e-8):
    """Mean Absolute Percentage Error on raw-unit scale, excluding zero actuals.

    Args:
        y_true: Array of actual values (raw units, not log-transformed).
        y_pred: Array of predicted values (raw units).
        eps: Stabiliser added to denominator.

    Returns:
        Tuple of (mape_value: float, zero_fraction: float).
    """

def wmape(y_true, y_pred, eps=1e-8):
    """Weighted Mean Absolute Percentage Error (revenue-weighted).

    Args:
        y_true: Array of actual values.
        y_pred: Array of predicted values.
        eps: Stabiliser for zero-sum guard.

    Returns:
        wmape_value as float.
    """

# search.py
def randomized_grid_search(estimator, param_grid, X_train, y_train,
                            n_iter, cv_splits, scoring, random_state,
                            mlflow_run_name):
    """Run RandomizedSearchCV with TimeSeriesSplit and log to MLflow.

    Args:
        estimator: Unfitted XGBoost estimator.
        param_grid: Dict of hyperparameter distributions from conf.
        X_train: Feature matrix.
        y_train: Target series.
        n_iter: Number of random parameter settings sampled.
        cv_splits: Number of TimeSeriesSplit folds.
        scoring: sklearn scoring string, e.g. "neg_mean_absolute_error".
        random_state: Reproducibility seed.
        mlflow_run_name: Name for the MLflow run.

    Returns:
        Best fitted estimator.
    """

# regressor.py
def train_regressor(df_train, df_eval, feature_cols, target_col,
                    param_grid, cfg, model_name):
    """Train and evaluate a single-stage XGBoost regressor with grid search.

    Args:
        df_train: Training DataFrame.
        df_eval: Evaluation DataFrame.
        feature_cols: List of input feature column names.
        target_col: Target column name (log-transformed).
        param_grid: Hyperparameter search space dict.
        cfg: Full conf dict.
        model_name: Identifier used for MLflow and .pkl filename.

    Returns:
        Fitted XGBRegressor (best model from search).
    """

# classifier.py
def train_classifier(df_train, df_eval, feature_cols, target_col,
                     param_grid, cfg, model_name):
    """Train and evaluate Stage-1 XGBoost binary classifier for lumpy demand.

    Args:
        df_train: Training DataFrame.
        df_eval: Evaluation DataFrame.
        feature_cols: List of input feature column names.
        target_col: Binary target column name (target_is_nonzero).
        param_grid: Hyperparameter search space dict.
        cfg: Full conf dict.
        model_name: Identifier used for MLflow and .pkl filename.

    Returns:
        Fitted XGBClassifier (best model from search).
    """

# two_stage.py
def train_two_stage(df_train, df_eval, feature_cols, cfg, model_name_prefix):
    """Train the two-stage classifier+regressor for lumpy demand cells.

    Stage 1: XGBClassifier on target_is_nonzero.
    Stage 2: XGBRegressor on target_qty_log1p, trained only on nonzero-demand rows.

    Args:
        df_train: Training DataFrame (full cell).
        df_eval: Evaluation DataFrame.
        feature_cols: Feature column list (same for both stages).
        cfg: Full conf dict.
        model_name_prefix: Prefix for both stage model files, e.g. "model_6_hva_lumpy".

    Returns:
        Tuple of (stage1_classifier, stage2_regressor).
    """

def predict_two_stage(clf, reg, X, threshold):
    """Generate combined two-stage prediction.

    Args:
        clf: Fitted Stage-1 XGBClassifier.
        reg: Fitted Stage-2 XGBRegressor.
        X: Feature matrix.
        threshold: Classifier probability threshold for nonzero prediction.

    Returns:
        Array of predicted raw quantities (0 where Stage 1 predicts zero event).
    """

# model_io.py
def save_model(model, output_dir, model_name):
    """Serialise a fitted model to .pkl.

    Args:
        model: Fitted estimator (XGBRegressor or XGBClassifier).
        output_dir: Directory path for output.
        model_name: Base filename without extension.

    Returns:
        Path to saved .pkl file.
    """

def load_model(output_dir, model_name):
    """Load a .pkl model from disk.

    Args:
        output_dir: Directory containing the .pkl file.
        model_name: Base filename without extension.

    Returns:
        Fitted estimator.
    """
```

---

## 7. Pipeline Layout — `pipelines/6_modeling/`

```
pipelines/6_modeling/
├── model_1_power_continuous.ipynb
├── model_2_power_intermittent.ipynb
├── model_3_power_lumpy.ipynb
├── model_4_hva_continuous.ipynb
├── model_5_hva_intermittent.ipynb
├── model_6_hva_lumpy.ipynb          ← two-stage
├── model_7_lvs_continuous.ipynb
├── model_8_lvs_intermittent.ipynb
└── model_9_lvs_lumpy.ipynb          ← two-stage
```

---

## 8. Notebook Template Structure

Every notebook follows this exact cell structure. The only difference between notebooks is the **CONFIGURABLE VARIABLES** block (Cell 2).

### Cell 1 — Imports and path setup
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path().resolve().parent.parent))

import numpy as np
import pandas as pd
import mlflow
from src.common.utils.config import load_config
from src.modeling.data_loader    import load_cell
from src.modeling.feature_selector import get_feature_columns
from src.modeling.splitter       import time_split
from src.modeling.metrics        import mape, wmape
from src.modeling.regressor      import train_regressor
from src.modeling.classifier     import train_classifier
from src.modeling.two_stage      import train_two_stage
from src.modeling.model_io       import save_model
```

### Cell 2 — Configurable variables (ONLY cell that changes per notebook)
```python
# === CONFIGURABLE VARIABLES — edit these for each model cell ===
CLUSTER_NAME = "Power"          # "Power" | "High-Value Active" | "Low-Value Sporadic"
DEMAND_CLASS = "Continuous"     # "Continuous" | "Intermittent" | "Lumpy"
GRID_CELL    = 0                # see mapping table below

# Grid cell reference:
# cluster \ demand   Continuous  Intermittent  Lumpy
# Power                  0            1           2
# High-Value Active      3            4           5   ← two-stage
# Low-Value Sporadic     6            7           8   ← two-stage
MODEL_NAME = f"model_{GRID_CELL}_{CLUSTER_NAME.lower().replace(' ', '_')}_{DEMAND_CLASS.lower()}"
IS_TWO_STAGE = GRID_CELL in {5, 8}
```

### Cell 3 — Load config and data
```python
cfg = load_config()
mod_cfg = cfg["modeling"]

matrix_path = Path(cfg["data"]["intermediate_path"]) / "full_reduced_modeling_matrix.parquet"
df = load_cell(matrix_path, CLUSTER_NAME, DEMAND_CLASS)
print(f"Cell rows: {len(df):,} | Columns: {df.shape[1]}")
```

### Cell 4 — Split
```python
df_train, df_eval = time_split(df, mod_cfg["train_end"], mod_cfg["eval_start"])
print(f"Train: {len(df_train):,} rows ({mod_cfg['train_start']} – {mod_cfg['train_end']})")
print(f"Eval:  {len(df_eval):,} rows ({mod_cfg['eval_start']} – {mod_cfg['eval_end']})")
```

### Cell 5 — Feature selection
```python
# For two-stage models, feature_cols are shared across both stages
target_col    = mod_cfg["target_regressor"]
feature_cols, target_col = get_feature_columns(df_train, target_col, mod_cfg["drop_columns"])
print(f"Feature count: {len(feature_cols)}")
```

### Cell 6 — Train
```python
mlflow.set_tracking_uri(mod_cfg["mlflow_tracking_uri"])
mlflow.set_experiment(mod_cfg["mlflow_experiment"])

if IS_TWO_STAGE:
    clf, reg = train_two_stage(df_train, df_eval, feature_cols, cfg, MODEL_NAME)
else:
    reg = train_regressor(
        df_train, df_eval, feature_cols, target_col,
        mod_cfg["xgb_param_grid"], cfg, MODEL_NAME
    )
    clf = None
```

### Cell 7 — Evaluate
```python
from src.modeling.two_stage import predict_two_stage

X_eval = df_eval[feature_cols].values
y_true_log  = df_eval[mod_cfg["target_regressor"]].values
y_true_raw  = df_eval["target_qty_raw"].values

if IS_TWO_STAGE:
    y_pred_raw = predict_two_stage(clf, reg, X_eval, mod_cfg["classifier_threshold"])
else:
    y_pred_log = reg.predict(X_eval)
    y_pred_raw = np.expm1(y_pred_log)

mape_val, zero_frac = mape(y_true_raw, y_pred_raw)
wmape_val = wmape(y_true_raw, y_pred_raw)
print(f"MAPE  : {mape_val:.2f}%  (zero actuals excluded: {zero_frac:.1%})")
print(f"WMAPE : {wmape_val:.2f}%")
```

### Cell 8 — Save models
```python
output_dir = Path(mod_cfg["model_output_path"])
if IS_TWO_STAGE:
    save_model(clf, output_dir, f"{MODEL_NAME}_stage1_clf")
    save_model(reg, output_dir, f"{MODEL_NAME}_stage2_reg")
else:
    save_model(reg, output_dir, MODEL_NAME)
print(f"Model(s) saved to {output_dir}")
```

---

## 9. The 9 Model Cells — Detailed Instructions

### Model 1 — Power + Continuous  (`grid_cell = 0`)
- **Notebook:** `pipelines/6_modeling/model_1_power_continuous.ipynb`
- **Type:** XGBoost Regressor
- **Target:** `target_qty_log1p`
- **Filter:** `cluster_definition == "Power"` AND `demand_class == "Continuous"`
- **Feature emphasis:** Seasonal lag features (`lag_sales_12m`, `seasonal_index`, Fourier terms, `is_peak_month`) are most important here. STL analysis showed seasonal strength 0.936 for this segment.
- **MLflow run name:** `model_1_power_continuous`
- **Output pkl:** `data/output/models/model_1_power_continuous.pkl`

---

### Model 2 — Power + Intermittent  (`grid_cell = 1`)
- **Notebook:** `pipelines/6_modeling/model_2_power_intermittent.ipynb`
- **Type:** XGBoost Regressor
- **Target:** `target_qty_log1p`
- **Filter:** `cluster_definition == "Power"` AND `demand_class == "Intermittent"`
- **Feature emphasis:** Rolling aggregate features (`roll_mean_qty_3m`, `roll_nonzero_count_12m`, `demand_event_rate_6m`) and larger time windows for sparse demand capture.
- **MLflow run name:** `model_2_power_intermittent`
- **Output pkl:** `data/output/models/model_2_power_intermittent.pkl`
- **Metrics note:** Report MAPE only on non-zero actuals. Report zero-demand fraction alongside.

---

### Model 3 — Power + Lumpy  (`grid_cell = 2`)
- **Notebook:** `pipelines/6_modeling/model_3_power_lumpy.ipynb`
- **Type:** XGBoost Regressor (single-stage; Power outlets have sufficient volume for direct regression)
- **Target:** `target_qty_log1p`
- **Filter:** `cluster_definition == "Power"` AND `demand_class == "Lumpy"`
- **Feature emphasis:** Same as Intermittent. Zero-inflation features (`months_since_last_purchase`, `demand_event_rate_6m`) critical.
- **MLflow run name:** `model_3_power_lumpy`
- **Output pkl:** `data/output/models/model_3_power_lumpy.pkl`
- **Metrics note:** Same zero-demand fraction caveat as Model 2.

---

### Model 4 — High-Value Active + Continuous  (`grid_cell = 3`)
- **Notebook:** `pipelines/6_modeling/model_4_hva_continuous.ipynb`
- **Type:** XGBoost Regressor
- **Target:** `target_qty_log1p`
- **Filter:** `cluster_definition == "High-Value Active"` AND `demand_class == "Continuous"`
- **Feature emphasis:** Seasonal features + outlet behaviour features (`outlet_loyalty_ratio`, `outlet_momentum`).
- **MLflow run name:** `model_4_hva_continuous`
- **Output pkl:** `data/output/models/model_4_hva_continuous.pkl`

---

### Model 5 — High-Value Active + Intermittent  (`grid_cell = 4`)
- **Notebook:** `pipelines/6_modeling/model_5_hva_intermittent.ipynb`
- **Type:** XGBoost Regressor
- **Target:** `target_qty_log1p`
- **Filter:** `cluster_definition == "High-Value Active"` AND `demand_class == "Intermittent"`
- **Feature emphasis:** Rolling aggregates, zero-inflation features, `short_long_ratio`.
- **MLflow run name:** `model_5_hva_intermittent`
- **Output pkl:** `data/output/models/model_5_hva_intermittent.pkl`

---

### Model 6 — High-Value Active + Lumpy  (`grid_cell = 5`)  ★ Two-Stage
- **Notebook:** `pipelines/6_modeling/model_6_hva_lumpy.ipynb`
- **Type:** XGBoost Classifier (Stage 1) + XGBoost Regressor (Stage 2)
- **Stage 1:**
  - Target: `target_is_nonzero` (binary)
  - Training data: all rows in cell (both zero and nonzero demand)
  - Handle class imbalance: set `scale_pos_weight = count(zero) / count(nonzero)` automatically in `train_classifier()`
  - Scoring: `f1` (balanced for imbalanced classes)
- **Stage 2:**
  - Target: `target_qty_log1p`
  - Training data: **only rows where `target_is_nonzero == 1`** (nonzero demand events only)
  - This avoids zero-inflation bias in the regressor
  - Scoring: `neg_mean_absolute_error`
- **Prediction:**
  - Stage 1 predicts P(nonzero); if ≥ threshold → Stage 2 predicts quantity
  - If < threshold → predict 0
- **Filter:** `cluster_definition == "High-Value Active"` AND `demand_class == "Lumpy"`
- **MLflow run name prefix:** `model_6_hva_lumpy`
- **Output pkl:**
  - `data/output/models/model_6_hva_lumpy_stage1_clf.pkl`
  - `data/output/models/model_6_hva_lumpy_stage2_reg.pkl`

---

### Model 7 — Low-Value Sporadic + Continuous  (`grid_cell = 6`)
- **Notebook:** `pipelines/6_modeling/model_7_lvs_continuous.ipynb`
- **Type:** XGBoost Regressor
- **Target:** `target_qty_log1p`
- **Filter:** `cluster_definition == "Low-Value Sporadic"` AND `demand_class == "Continuous"`
- **Feature emphasis:** Seasonal features; LVS outlets have infrequent purchase so `outlet_avg_txn_per_active_month` and `outlet_loyalty_ratio` are useful segment discriminators.
- **MLflow run name:** `model_7_lvs_continuous`
- **Output pkl:** `data/output/models/model_7_lvs_continuous.pkl`

---

### Model 8 — Low-Value Sporadic + Intermittent  (`grid_cell = 7`)
- **Notebook:** `pipelines/6_modeling/model_8_lvs_intermittent.ipynb`
- **Type:** XGBoost Regressor
- **Target:** `target_qty_log1p`
- **Filter:** `cluster_definition == "Low-Value Sporadic"` AND `demand_class == "Intermittent"`
- **Feature emphasis:** Same as Model 5. `demand_event_rate_6m` and `months_since_last_purchase` are critical given sparse buying behaviour of LVS.
- **MLflow run name:** `model_8_lvs_intermittent`
- **Output pkl:** `data/output/models/model_8_lvs_intermittent.pkl`

---

### Model 9 — Low-Value Sporadic + Lumpy  (`grid_cell = 8`)  ★ Two-Stage
- **Notebook:** `pipelines/6_modeling/model_9_lvs_lumpy.ipynb`
- **Type:** XGBoost Classifier (Stage 1) + XGBoost Regressor (Stage 2)
- **Same architecture as Model 6.** Highest zero-inflation in the grid — `scale_pos_weight` will be largest here.
- **Filter:** `cluster_definition == "Low-Value Sporadic"` AND `demand_class == "Lumpy"`
- **MLflow run name prefix:** `model_9_lvs_lumpy`
- **Output pkl:**
  - `data/output/models/model_9_lvs_lumpy_stage1_clf.pkl`
  - `data/output/models/model_9_lvs_lumpy_stage2_reg.pkl`

---

## 10. MLflow Logging Spec

Every training run must log the following to MLflow:

### Parameters (logged automatically by `randomized_grid_search`)
- All best hyperparameters from grid search
- `cluster_name`, `demand_class`, `grid_cell`, `model_type`
- `train_start`, `train_end`, `eval_start`, `eval_end`
- `n_iter`, `cv_splits`

### Metrics (logged in `train_regressor` / `train_classifier` / `train_two_stage`)
- `eval_wmape` (primary)
- `eval_mape` (non-zero actuals only)
- `eval_zero_fraction` (fraction of eval rows with zero actual demand)
- `eval_mae` (on log scale for regressors)
- `eval_rmse` (on log scale for regressors)
- `train_wmape`, `train_mape` (for overfitting check)
- For classifiers: `eval_f1`, `eval_precision`, `eval_recall`, `eval_auc`

### Artifacts
- Best model saved as `.pkl` (via `model_io.save_model`)
- Feature importance plot (optional, saves as `feature_importance.png`)

---

## 11. Feature Set — What to Drop per Model

`get_feature_columns()` in `feature_selector.py` assembles the drop list dynamically from `conf.modeling.drop_columns`. The logic:

```
all_drop = (
    identifiers
    + geo_admin
    + product_admin
    + segment_strings
    + all target columns EXCEPT the active target
)
feature_cols = [c for c in df.columns if c not in all_drop]
```

For **regressor models**: active target = `target_qty_log1p`; drop `target_qty_raw`, `target_is_nonzero`, `target_log1p_net_sales`.

For **Stage-1 classifier**: active target = `target_is_nonzero`; drop `target_qty_raw`, `target_qty_log1p`, `target_log1p_net_sales`.

For **Stage-2 regressor**: active target = `target_qty_log1p`; same drop list as regressor models (applied after filtering to nonzero rows).

---

## 12. Implementation Order

Implement in this order to avoid rework:

1. `conf/conf.yml` — add `modeling:` block
2. `src/modeling/__init__.py`
3. `src/modeling/metrics.py` — no dependencies
4. `src/modeling/model_io.py` — no dependencies
5. `src/modeling/data_loader.py`
6. `src/modeling/feature_selector.py`
7. `src/modeling/splitter.py`
8. `src/modeling/search.py`
9. `src/modeling/regressor.py`
10. `src/modeling/classifier.py`
11. `src/modeling/two_stage.py`
12. Notebooks: start with `model_1_power_continuous.ipynb` to validate end-to-end, then replicate for remaining 8.

---

## 13. Model File Naming Convention

```
data/output/models/
├── model_1_power_continuous.pkl
├── model_2_power_intermittent.pkl
├── model_3_power_lumpy.pkl
├── model_4_hva_continuous.pkl
├── model_5_hva_intermittent.pkl
├── model_6_hva_lumpy_stage1_clf.pkl
├── model_6_hva_lumpy_stage2_reg.pkl
├── model_7_lvs_continuous.pkl
├── model_8_lvs_intermittent.pkl
├── model_9_lvs_lumpy_stage1_clf.pkl
└── model_9_lvs_lumpy_stage2_reg.pkl
```

---

## 14. Checklist Before Calling "Model N Complete"

- [ ] Notebook runs end-to-end without errors
- [ ] Train/eval split uses date boundary, not random
- [ ] No target leakage columns in feature matrix
- [ ] Territory/geo/product_admin columns excluded
- [ ] MLflow run visible in `mlruns/` with params, metrics, and artifact
- [ ] `eval_wmape` logged and reasonable (< 60% for Continuous, < 80% for Lumpy acceptable for baseline)
- [ ] Model `.pkl` saved to `data/output/models/`
- [ ] Two-stage models save both stage files separately

---

*Prepared: 2026-05-02. To implement: say "refer to docs/13_modeling_implementation.md and implement Model N" for any cell.*
