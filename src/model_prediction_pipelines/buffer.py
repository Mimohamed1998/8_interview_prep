"""Buffer mechanism: adjusts forecasts using the rolling 2-month mean error."""

import glob

import numpy as np
import pandas as pd


def load_actuals(cell_data_path: str) -> pd.DataFrame:
    """Concatenate target_qty_raw from all 9 cell parquets.

    Args:
        cell_data_path: Directory containing ``cell_*.parquet`` files.

    Returns:
        DataFrame with ``outlet_id``, ``item_code``, ``year_month``, ``actual_qty``.
    """
    frames = []
    for path in glob.glob(f"{cell_data_path}/cell_*.parquet"):
        df = pd.read_parquet(path, columns=["outlet_id", "item_code", "year_month", "target_qty_raw"])
        frames.append(df)
    actuals = pd.concat(frames, ignore_index=True)
    actuals = actuals.rename(columns={"target_qty_raw": "actual_qty"})
    actuals = actuals.drop_duplicates(subset=["outlet_id", "item_code", "year_month"])
    return actuals


def compute_buffer(df: pd.DataFrame, n_months: int = 2) -> pd.DataFrame:
    """Add a ``buffer`` column = rolling mean of the last *n_months* errors.

    Error is defined as ``actual_qty - predicted_qty`` (positive = under-forecast).
    The buffer for month T uses errors from months T-n_months … T-1 (shifted,
    never including T itself).

    Args:
        df: DataFrame with ``outlet_id``, ``item_code``, ``year_month``,
            ``predicted_qty``, and ``actual_qty``.  Must already be joined.
        n_months: Look-back window (default 2).

    Returns:
        Same DataFrame with two new columns added:
        ``error`` (actual − predicted) and ``buffer`` (rolling mean error,
        filled with 0 where insufficient history exists).
    """
    df = df.sort_values(["outlet_id", "item_code", "year_month"]).copy()
    df["error"] = df["actual_qty"] - df["predicted_qty"]

    df["buffer"] = (
        df.groupby(["outlet_id", "item_code"])["error"]
        .transform(
            lambda s: s.shift(1).rolling(window=n_months, min_periods=1).mean()
        )
        .fillna(0.0)
    )
    return df


def apply_buffer(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the buffer to produce ``buffered_forecast`` (clipped ≥ 0).

    Args:
        df: Output of :func:`compute_buffer`.

    Returns:
        Same DataFrame with ``buffered_forecast`` column added.
    """
    df = df.copy()
    df["buffered_forecast"] = np.clip(df["predicted_qty"] + df["buffer"], 0, None)
    return df


def _wape(actual: pd.Series, forecast: pd.Series) -> float:
    """Weighted Absolute Percentage Error."""
    denom = actual.sum()
    if denom == 0:
        return np.nan
    return (actual - forecast).abs().sum() / denom


def _mape(actual: pd.Series, forecast: pd.Series) -> float:
    """Mean Absolute Percentage Error (excludes zero-actual rows)."""
    mask = actual > 0
    if mask.sum() == 0:
        return np.nan
    return ((actual[mask] - forecast[mask]).abs() / actual[mask]).mean()


def compute_metrics(df: pd.DataFrame, eval_start: str, eval_end: str) -> pd.DataFrame:
    """Compute WAPE and MAPE before and after the buffer on the eval window.

    Args:
        df: Output of :func:`apply_buffer` — must contain ``actual_qty``,
            ``predicted_qty``, ``buffered_forecast``, and ``year_month``.
        eval_start: Inclusive start of evaluation window (``"YYYY-MM"``).
        eval_end: Inclusive end of evaluation window (``"YYYY-MM"``).

    Returns:
        DataFrame with one row each for raw and buffered metrics.
    """
    mask = (df["year_month"] >= eval_start) & (df["year_month"] <= eval_end)
    eval_df = df[mask]

    rows = [
        {
            "forecast_type": "raw",
            "wape": _wape(eval_df["actual_qty"], eval_df["predicted_qty"]),
            "mape": _mape(eval_df["actual_qty"], eval_df["predicted_qty"]),
        },
        {
            "forecast_type": "buffered",
            "wape": _wape(eval_df["actual_qty"], eval_df["buffered_forecast"]),
            "mape": _mape(eval_df["actual_qty"], eval_df["buffered_forecast"]),
        },
    ]
    return pd.DataFrame(rows)


def build_buffer_output(df: pd.DataFrame) -> pd.DataFrame:
    """Return the slim output table: primary keys + forecast + buffer + actuals + errors.

    Args:
        df: Output of :func:`apply_buffer`.

    Returns:
        DataFrame with columns: ``outlet_id``, ``item_code``, ``year_month``,
        ``actual_qty``, ``predicted_qty``, ``buffer``, ``buffered_forecast``,
        ``abs_error_raw``, ``abs_error_buffered``.
    """
    out = df[["outlet_id", "item_code", "year_month", "actual_qty",
              "predicted_qty", "buffer", "buffered_forecast"]].copy()
    out["abs_error_raw"] = (out["actual_qty"] - out["predicted_qty"]).abs()
    out["abs_error_buffered"] = (out["actual_qty"] - out["buffered_forecast"]).abs()
    return out
