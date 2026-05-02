"""Inference helpers for the 9-cell demand forecasting pipeline."""

import numpy as np
import pandas as pd

from src.modeling.model_io import load_model
from src.modeling.feature_selector import get_feature_columns
from src.modeling.two_stage import predict_two_stage


CELL_REGISTRY = [
    {"cell_file": "cell_0_power_continuous.parquet",        "model_name": "model_0_power_continuous",        "lumpy": False},
    {"cell_file": "cell_1_power_intermittent.parquet",      "model_name": "model_1_power_intermittent",      "lumpy": False},
    {"cell_file": "cell_2_power_lumpy.parquet",             "model_name": "model_2_power_lumpy",             "lumpy": False},
    {"cell_file": "cell_3_high-value_active_continuous.parquet",    "model_name": "model_3_high-value_active_continuous",    "lumpy": False},
    {"cell_file": "cell_4_high-value_active_intermittent.parquet",  "model_name": "model_4_high-value_active_intermittent",  "lumpy": False},
    {"cell_file": "cell_5_high-value_active_lumpy.parquet",         "model_name": "model_5_high-value_active_lumpy",         "lumpy": True},
    {"cell_file": "cell_6_low-value_sporadic_continuous.parquet",   "model_name": "model_6_low-value_sporadic_continuous",   "lumpy": False},
    {"cell_file": "cell_7_low-value_sporadic_intermittent.parquet", "model_name": "model_7_low-value_sporadic_intermittent", "lumpy": False},
    {"cell_file": "cell_8_low-value_sporadic_lumpy.parquet",        "model_name": "model_8_low-value_sporadic_lumpy",        "lumpy": True},
]


def filter_inference_window(df, start, end):
    """Filter a DataFrame to rows within the inference year_month window.

    Args:
        df: DataFrame with a string ``year_month`` column (``"YYYY-MM"`` format).
        start: Inclusive start period, e.g. ``"2018-10"``.
        end: Inclusive end period, e.g. ``"2019-12"``.

    Returns:
        Filtered DataFrame.
    """
    return df[(df["year_month"] >= start) & (df["year_month"] <= end)].copy()


def predict_cell(df_infer, model_path, cell_meta, mod_cfg):
    """Load the model(s) for one grid cell and return a prediction DataFrame.

    For single-stage cells the regressor is applied directly; for two-stage
    (lumpy) cells the classifier gates the regressor.

    Args:
        df_infer: Inference-window DataFrame for this cell.
        model_path: Path to the directory containing ``.pkl`` model files.
        cell_meta: Dict entry from ``CELL_REGISTRY`` describing this cell.
        mod_cfg: ``cfg["modeling"]`` sub-dict supplying drop_columns, targets,
            and classifier_threshold.

    Returns:
        DataFrame with identifier columns plus ``predicted_qty``.
    """
    feature_cols, _ = get_feature_columns(
        df_infer, mod_cfg["target_regressor"], mod_cfg["drop_columns"]
    )
    X = df_infer[feature_cols].values.astype("float32")
    X[np.isinf(X)] = np.nan

    if cell_meta["lumpy"]:
        clf = load_model(model_path, f"{cell_meta['model_name']}_stage1_clf")
        reg = load_model(model_path, f"{cell_meta['model_name']}_stage2_reg")
        y_pred = predict_two_stage(clf, reg, X, mod_cfg["classifier_threshold"])
    else:
        reg = load_model(model_path, cell_meta["model_name"])
        y_pred = np.clip(reg.predict(X), 0, None)

    result = df_infer[["outlet_id", "item_code", "year_month"]].copy()
    result["predicted_qty"] = y_pred
    return result


def run_inference(cfg):
    """Run inference across all 9 grid cells and return the combined predictions.

    Reads each cached cell parquet, filters to the inference window defined in
    ``cfg["inference"]``, scores with the corresponding model(s), and
    concatenates all cell predictions into one DataFrame.

    Args:
        cfg: Full project config dict (output of ``load_config()``).

    Returns:
        DataFrame with columns ``outlet_id``, ``item_code``, ``year_month``,
        ``predicted_qty``, and ``cell_name``.
    """
    inf_cfg = cfg["inference"]
    mod_cfg = cfg["modeling"]
    cell_data_path = inf_cfg["cell_data_path"]
    model_path = inf_cfg["model_path"]
    start = inf_cfg["start"]
    end = inf_cfg["end"]

    frames = []
    for cell_meta in CELL_REGISTRY:
        df_raw = pd.read_parquet(f"{cell_data_path}/{cell_meta['cell_file']}")
        df_infer = filter_inference_window(df_raw, start, end)
        df_pred = predict_cell(df_infer, model_path, cell_meta, mod_cfg)
        df_pred["cell_name"] = cell_meta["cell_file"].replace(".parquet", "")
        frames.append(df_pred)

    return pd.concat(frames, ignore_index=True)
