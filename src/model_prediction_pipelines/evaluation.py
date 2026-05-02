"""Cohort-level evaluation: per-item and per-outlet-cluster WAPE / MAPE."""

import numpy as np
import pandas as pd


def _wape(actual: pd.Series, forecast: pd.Series) -> float:
    denom = actual.sum()
    return np.nan if denom == 0 else (actual - forecast).abs().sum() / denom


def _mape(actual: pd.Series, forecast: pd.Series) -> float:
    mask = actual > 0
    if mask.sum() == 0:
        return np.nan
    return ((actual[mask] - forecast[mask]).abs() / actual[mask]).mean()


def _eval_group(grp: pd.DataFrame) -> pd.Series:
    """Compute all evaluation metrics for one cohort group."""
    return pd.Series({
        "n_rows":             len(grp),
        "total_actual":       grp["actual_qty"].sum(),
        "total_forecast_raw": grp["predicted_qty"].sum(),
        "total_forecast_buf": grp["buffered_forecast"].sum(),
        "wape_raw":           _wape(grp["actual_qty"], grp["predicted_qty"]),
        "mape_raw":           _mape(grp["actual_qty"], grp["predicted_qty"]),
        "wape_buffered":      _wape(grp["actual_qty"], grp["buffered_forecast"]),
        "mape_buffered":      _mape(grp["actual_qty"], grp["buffered_forecast"]),
        "mean_abs_error_raw": grp["abs_error_raw"].mean(),
        "mean_abs_error_buf": grp["abs_error_buffered"].mean(),
    })


def evaluate_by_item(
    df: pd.DataFrame,
    item_meta: pd.DataFrame,
    eval_start: str,
    eval_end: str,
) -> pd.DataFrame:
    """Per-item evaluation metrics on the eval window.

    Args:
        df: Output of the buffer pipeline (predictions_buffered.parquet).
        item_meta: DataFrame with ``item_code`` and ``demand_class`` columns.
        eval_start: Inclusive eval start (``"YYYY-MM"``).
        eval_end: Inclusive eval end (``"YYYY-MM"``).

    Returns:
        DataFrame indexed by ``item_code`` with WAPE/MAPE columns for raw and
        buffered forecasts, sorted by ``wape_raw`` descending.
    """
    mask = (df["year_month"] >= eval_start) & (df["year_month"] <= eval_end)
    eval_df = df[mask].merge(item_meta, on="item_code", how="left")

    result = (
        eval_df.groupby("item_code", observed=True)
        .apply(_eval_group, include_groups=False)
        .reset_index()
        .merge(item_meta, on="item_code", how="left")
    )

    cols = [
        "item_code", "demand_class",
        "n_rows", "total_actual", "total_forecast_raw", "total_forecast_buf",
        "wape_raw", "mape_raw", "wape_buffered", "mape_buffered",
        "mean_abs_error_raw", "mean_abs_error_buf",
    ]
    return result[cols].sort_values("wape_raw", ascending=False).reset_index(drop=True)


def evaluate_by_outlet_cluster(
    df: pd.DataFrame,
    outlet_clusters: pd.DataFrame,
    eval_start: str,
    eval_end: str,
) -> pd.DataFrame:
    """Per-outlet-cluster evaluation metrics on the eval window.

    Args:
        df: Output of the buffer pipeline (predictions_buffered.parquet).
        outlet_clusters: DataFrame with ``outlet_id`` and ``cluster_definition``.
        eval_start: Inclusive eval start (``"YYYY-MM"``).
        eval_end: Inclusive eval end (``"YYYY-MM"``).

    Returns:
        DataFrame indexed by ``cluster_definition`` with WAPE/MAPE columns.
    """
    mask = (df["year_month"] >= eval_start) & (df["year_month"] <= eval_end)
    eval_df = df[mask].merge(outlet_clusters, on="outlet_id", how="left")

    result = (
        eval_df.groupby("cluster_definition", observed=True)
        .apply(_eval_group, include_groups=False)
        .reset_index()
    )

    result["n_outlets"] = (
        eval_df.groupby("cluster_definition", observed=True)["outlet_id"]
        .nunique()
        .reset_index(drop=True)
    )

    cols = [
        "cluster_definition",
        "n_outlets", "n_rows", "total_actual", "total_forecast_raw", "total_forecast_buf",
        "wape_raw", "mape_raw", "wape_buffered", "mape_buffered",
        "mean_abs_error_raw", "mean_abs_error_buf",
    ]
    return result[cols].sort_values("wape_raw", ascending=False).reset_index(drop=True)
