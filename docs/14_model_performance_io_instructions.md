# Model Performance & I/O Instructions — Demand Forecasting

**Author:** Mohamed Inas  
**Created:** 2026-05-02  
**Depends on:** `docs/13_modeling_implementation.md`  
**Model artifacts:** `data/output/models/`  
**MLflow tracking:** `pipelines/6_modeling/mlruns/`

---

## 1. The 3×3 Model Grid

Nine XGBoost models covering the cross of three outlet segments × three demand classes.

```
                     Continuous          Intermittent        Lumpy
Power                Model 1 (R)         Model 2 (R)         Model 3 (R)
High-Value Active    Model 4 (R)         Model 5 (R)         Model 6 (C+R)
Low-Value Sporadic   Model 7 (R)         Model 8 (R)         Model 9 (C+R)

R   = XGBoost Regressor (single-stage)
C+R = XGBoost Classifier (Stage 1) + XGBoost Regressor (Stage 2)
```

---

## 2. Metric Definitions

### MAPE — Mean Absolute Percentage Error
```
MAPE = mean(|actual − predicted| / (|actual| + ε)) × 100     ε = 1e-8
```
- Computed **only on non-zero actual rows** for Intermittent and Lumpy segments.
- Sensitive to small-volume observations; outlier-prone on sparse demand.
- Report alongside `zero_fraction` (share of eval rows where actual = 0) for context.

### WMAPE — Weighted Mean Absolute Percentage Error  *(primary metric)*
```
WMAPE = Σ|actual − predicted| / Σ(actual + ε) × 100
```
- Revenue-weighted: large-volume months drive the score, small-volume noise is dampened.
- Robust to zero-demand rows — can be computed on the full eval set without exclusions.
- Use **WMAPE as the headline metric** for comparing models and reporting to stakeholders.

---

## 3. Evaluation Results by Segment

Training window: **2015-01 → 2018-12** (48 months)  
Evaluation window: **2019-01 → 2019-12** (12 months)

All hyperparameter search used `RandomizedSearchCV` with `TimeSeriesSplit(n_splits=3)`.

### 3.1 Power Outlets

| Model | Demand Class | Type | MAPE | WMAPE | Artifact |
|-------|-------------|------|-----:|------:|---------|
| Model 1 | Continuous | Regressor | 74.49% | 145.38% | `model_1_power_continuous.pkl` |
| Model 2 | Intermittent | Regressor | 89.06% | 146.54% | `model_2_power_intermittent.pkl` |
| Model 3 | Lumpy | Regressor | 117.91% | 158.96% | `model_3_power_lumpy.pkl` |

> **Read-out:** Power is the most predictable segment. WMAPE stays below 160% across all demand classes. The Continuous sub-segment (Model 1) achieves the second-best WMAPE in the grid (145.38%), consistent with the high seasonal strength (0.936) observed in EDA. Lumpy demand (Model 3) degrades MAPE by ~58pp vs Continuous but WMAPE remains contained — Power outlets have enough volume to stabilise the weighted metric even when individual forecasts miss.

### 3.2 High-Value Active (HVA) Outlets

| Model | Demand Class | Type | MAPE | WMAPE | Stage 1 F1 | Artifact |
|-------|-------------|------|-----:|------:|:----------:|---------|
| Model 4 | Continuous | Regressor | 70.45% | 161.34% | — | `model_4_hva_continuous.pkl` |
| Model 5 | Intermittent | Regressor | 79.17% | 206.68% | — | `model_5_hva_intermittent.pkl` |
| Model 6 | Lumpy | Classifier + Regressor | 192.22% | 826.17% | 0.1941 | `model_6_hva_lumpy_stage1_clf.pkl` + `model_6_hva_lumpy_stage2_reg.pkl` |

> **Read-out:** HVA Continuous (Model 4) delivers the **best MAPE in the grid (70.45%)**. The outlet behaviour features (`outlet_loyalty_ratio`, `outlet_momentum`) appear to add useful signal for this segment. Performance degrades sharply at the Lumpy cell (Model 6): WMAPE jumps to 826%. This is primarily driven by the low Stage 1 F1 (0.19) — the classifier predicts the occurrence of a demand event poorly on this segment, so the two-stage pipeline frequently predicts zero when demand actually arrives (and vice versa). Consider revising the `scale_pos_weight` tuning or switching to a threshold-optimised F1 search for Stage 1.

### 3.3 Low-Value Sporadic (LVS) Outlets

| Model | Demand Class | Type | MAPE | WMAPE | Stage 1 F1 | Artifact |
|-------|-------------|------|-----:|------:|:----------:|---------|
| Model 7 | Continuous | Regressor | 76.86% | 200.56% | — | `model_7_lvs_continuous.pkl` |
| Model 8 | Intermittent | Regressor | 88.26% | 316.30% | — | `model_8_lvs_intermittent.pkl` |
| Model 9 | Lumpy | Classifier + Regressor | 122.25% | 1486.47% | 0.1203 | `model_9_lvs_lumpy_stage1_clf.pkl` + `model_9_lvs_lumpy_stage2_reg.pkl` |

> **Read-out:** LVS is the hardest segment. Even Continuous demand (Model 7) WMAPE exceeds 200% because LVS outlets buy infrequently and in small volumes — low-signal history makes forecasting structurally difficult. Model 9 (Lumpy) produces the **worst WMAPE in the grid (1486.47%)**. The Stage 1 F1 of 0.12 indicates near-random demand-event prediction on this tail segment. These models should be treated as directional signals rather than precise forecasts; ensemble or rule-based fallbacks (e.g., forward-fill last demand event × seasonal index) may outperform the learned model here.

---

## 4. Cross-Segment Summary Table

| Segment \ Demand | Continuous WMAPE | Intermittent WMAPE | Lumpy WMAPE |
|------------------|:----------------:|:-----------------:|:-----------:|
| **Power** | 145.38% | 146.54% | 158.96% |
| **High-Value Active** | 161.34% | 206.68% | 826.17% |
| **Low-Value Sporadic** | 200.56% | 316.30% | 1486.47% |

**Key patterns:**
1. WMAPE degrades from Power → HVA → LVS for every demand class — outlet volume is the dominant driver of forecastability.
2. Lumpy demand always has the highest error within its outlet row; the two-stage architecture introduces compounding misclassification error on top of quantity regression error.
3. MAPE and WMAPE diverge most severely in LVS-Lumpy (MAPE 122% vs WMAPE 1486%) because the model predicts near-zero for most rows, artificially lowering the unweighted MAPE while the weighted sum of errors is catastrophic.

---

## 5. Shared Best Hyperparameters

All nine models converged to the same best hyperparameter configuration from `RandomizedSearchCV`:

| Hyperparameter | Value |
|---|---|
| `n_estimators` | 200 |
| `max_depth` | 7 |
| `learning_rate` | 0.1 |
| `subsample` | 1.0 |
| `colsample_bytree` | 1.0 |
| `min_child_weight` | 5 |
| `reg_alpha` | 0 |
| `reg_lambda` | 0.5 |

> All models shared the same search space and random state (42). The identical best params suggest the search may not have been diverse enough to find segment-specific optima — widening `n_iter` or adding `gamma` / `scale_pos_weight` to the grid is recommended for the next iteration.

---

## 6. Loading Models — I/O Instructions

### Where models are stored

All models are saved as plain pkl files to:

```
/Users/mohamedinas/Desktop/SE_projects/8_stax_interview/8_interview_prep/data/output/models/
```

This is driven by `conf.yml` setting `model_output_path: "data/output/models"` (relative to the project root). File names use **0-indexed grid cell numbers** (matching `GRID_CELL` in each notebook) and full hyphenated cluster names.

> The MLflow `mlruns/` directory under `pipelines/6_modeling/` captures metrics and params only — it does **not** store the pkl files. Do not look for models there.

### 6.1 Single-Stage Regressor (Grid Cells 0–4, 6–7)

```python
from src.modeling.model_io import load_model

MODELS = "/Users/mohamedinas/Desktop/SE_projects/8_stax_interview/8_interview_prep/data/output/models"

reg0 = load_model(MODELS, "model_0_power_continuous")               # Power + Continuous
reg1 = load_model(MODELS, "model_1_power_intermittent")             # Power + Intermittent
reg2 = load_model(MODELS, "model_2_power_lumpy")                    # Power + Lumpy
reg3 = load_model(MODELS, "model_3_high-value_active_continuous")   # HVA + Continuous
reg4 = load_model(MODELS, "model_4_high-value_active_intermittent") # HVA + Intermittent
reg6 = load_model(MODELS, "model_6_low-value_sporadic_continuous")  # LVS + Continuous
reg7 = load_model(MODELS, "model_7_low-value_sporadic_intermittent")# LVS + Intermittent

y_pred = reg0.predict(X_eval)
```

### 6.2 Two-Stage Classifier + Regressor (Grid Cells 5 and 8)

Both two-stage models are present and ready to load.

```python
from src.modeling.model_io import load_model
from src.modeling.two_stage import predict_two_stage
from src.common.utils.config import load_config

cfg = load_config()
threshold = cfg["modeling"]["classifier_threshold"]   # default 0.5

MODELS = "/Users/mohamedinas/Desktop/SE_projects/8_stax_interview/8_interview_prep/data/output/models"

# Grid cell 5 — High-Value Active + Lumpy
clf5 = load_model(MODELS, "model_5_high-value_active_lumpy_stage1_clf")
reg5 = load_model(MODELS, "model_5_high-value_active_lumpy_stage2_reg")
y_pred5 = predict_two_stage(clf5, reg5, X_eval, threshold)

# Grid cell 8 — Low-Value Sporadic + Lumpy
clf8 = load_model(MODELS, "model_8_low-value_sporadic_lumpy_stage1_clf")
reg8 = load_model(MODELS, "model_8_low-value_sporadic_lumpy_stage2_reg")
y_pred8 = predict_two_stage(clf8, reg8, X_eval, threshold)
```

### 6.3 Feature Matrix Requirements

Before calling `.predict()`, the input `X_eval` must:

1. **Contain the same columns** as the training feature matrix — use `get_feature_columns()` with the same `drop_cfg` from conf.
2. **Exclude all forbidden columns:** `outlet_id`, `item_code`, `year_month`, `territory_id`, `region`, `district`, `province`, `product_category`, `product_line`, `brand`, `cluster_definition`, `demand_class`, and all target columns.
3. **Be filtered to the correct grid cell** — the model was trained only on rows matching its `(cluster_definition, demand_class)` pair. Mixing segments will silently produce incorrect predictions.
4. **Not be log-transformed** — all models predict `target_qty_raw` (raw units). Apply `np.clip(y_pred, 0, None)` post-prediction if negative outputs appear.

```python
from src.modeling.data_loader import load_cell
from src.modeling.feature_selector import get_feature_columns

df = load_cell(matrix_path, cluster_name="Power", demand_class="Continuous")
feature_cols, _ = get_feature_columns(df, target_col="target_qty_raw", drop_cfg=cfg["modeling"]["drop_columns"])

X = df[feature_cols].values
y_pred = reg.predict(X)
```

### 6.4 Artifact Availability Status

Output directory: `/Users/mohamedinas/Desktop/SE_projects/8_stax_interview/8_interview_prep/data/output/models/`

| Grid Cell | Segment | Demand Class | Filename | Status |
|:---------:|---------|-------------|----------|:------:|
| 0 | Power | Continuous | `model_0_power_continuous.pkl` | ✓ |
| 1 | Power | Intermittent | `model_1_power_intermittent.pkl` | ✓ |
| 2 | Power | Lumpy | `model_2_power_lumpy.pkl` | ✓ |
| 3 | High-Value Active | Continuous | `model_3_high-value_active_continuous.pkl` | ✓ |
| 4 | High-Value Active | Intermittent | `model_4_high-value_active_intermittent.pkl` | ✓ |
| 5 | High-Value Active | Lumpy | `model_5_high-value_active_lumpy_stage1_clf.pkl` + `_stage2_reg.pkl` | ✓ |
| 6 | Low-Value Sporadic | Continuous | `model_6_low-value_sporadic_continuous.pkl` | ✓ |
| 7 | Low-Value Sporadic | Intermittent | `model_7_low-value_sporadic_intermittent.pkl` | ✓ |
| 8 | Low-Value Sporadic | Lumpy | `model_8_low-value_sporadic_lumpy_stage1_clf.pkl` + `_stage2_reg.pkl` | ✓ |

All 11 pkl files present (9 grid cells; cells 5 and 8 produce 2 files each).

---

## 7. Interpreting MAPE vs WMAPE — Guidance by Demand Class

| Demand Class | Use MAPE when… | Use WMAPE when… |
|---|---|---|
| **Continuous** | Diagnosing per-observation forecast quality; no zero exclusions needed | Reporting headline performance; all rows contribute |
| **Intermittent** | Checking accuracy on active demand months only (MAPE excludes zeros by design) | Evaluating overall business impact including zero-demand periods |
| **Lumpy** | MAPE is the less reliable metric here — report zero_fraction alongside | **Always prefer WMAPE** — zero-dominant rows dominate MAPE numerically; WMAPE naturally discounts them |

> For two-stage models (6, 9): Stage 1 F1 measures how well the classifier detects demand events. Low F1 (< 0.3) means the quantity prediction from Stage 2 rarely fires — the final combined WMAPE is dominated by false-zero predictions, not regression error. Fix Stage 1 first before tuning Stage 2.

---

## 8. MLflow — Viewing Run History

```bash
# From repo root
cd pipelines/6_modeling
mlflow ui --backend-store-uri mlruns --port 5000
```

Open `http://localhost:5000` → experiment `demand_forecasting` → filter by `model_name` tag to compare runs per grid cell. The primary sort metric is `eval_wmape`.

---

*Prepared: 2026-05-02. Supersedes the metrics checklist in `docs/13_modeling_implementation.md` Section 14.*
