import pandas as pd
import json
import math
from typing import Dict, List, Any

def analyze_dataset(path: str) -> Dict[str, Any]:
    """
    Analyze a dataset for data quality metrics.

    Args:
        path: Path to the dataset file (CSV, Parquet, Excel, JSON).

    Returns:
        Dictionary with analysis results including shape, columns info, etc.
    """
    ext = path.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        df = pd.read_csv(path)
    elif ext == "parquet":
        df = pd.read_parquet(path)
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(path)
    elif ext == "json":
        df = pd.read_json(path)
    else:
        raise ValueError(f"Unsupported extension: {ext}")

    n_rows, n_cols = df.shape
    result = {"n_rows": n_rows, "n_cols": n_cols, "columns": []}

    CATEGORICAL_THRESHOLD = 50

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        null_pct = round(null_count / n_rows * 100, 2) if n_rows else 0
        dtype = str(series.dtype)
        n_unique = int(series.nunique(dropna=True))
        is_numeric = pd.api.types.is_numeric_dtype(series)

        col_info = {
            "name": col, "dtype": dtype,
            "null_count": null_count, "null_pct": null_pct, "n_unique": n_unique,
        }

        if is_numeric:
            desc = series.describe()
            col_info["stats"] = {
                "mean":   round(float(desc["mean"]), 4) if not math.isnan(desc["mean"]) else None,
                "std":    round(float(desc["std"]),  4) if not math.isnan(desc["std"])  else None,
                "min":    round(float(desc["min"]),  4),
                "p25":    round(float(desc["25%"]),  4),
                "median": round(float(desc["50%"]),  4),
                "p75":    round(float(desc["75%"]),  4),
                "max":    round(float(desc["max"]),  4),
            }
        elif n_unique <= CATEGORICAL_THRESHOLD:
            vc = series.value_counts(dropna=False).head(30)
            col_info["top_values"] = [
                {"value": str(k), "count": int(v), "pct": round(int(v)/n_rows*100, 2)}
                for k, v in vc.items()
            ]

        result["columns"].append(col_info)

    return result

def detect_dq_issues(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect data quality issues based on analysis.

    Args:
        analysis: Output from analyze_dataset.

    Returns:
        List of issue dictionaries.
    """
    issues = []
    n_rows = analysis["n_rows"]

    for col in analysis["columns"]:
        name = col["name"]
        null_pct = col["null_pct"]
        n_unique = col["n_unique"]
        is_numeric = "stats" in col

        # High nulls
        if null_pct > 20:
            issues.append({
                "col": name,
                "issue": "High nulls",
                "detail": f"{null_pct}% missing",
                "severity": "High",
                "remedy": "Drop column if low value; otherwise impute with median (numeric) or mode (categorical). Investigate upstream pipeline."
            })

        # Moderate nulls
        elif 5 < null_pct <= 20:
            issues.append({
                "col": name,
                "issue": "Moderate nulls",
                "detail": f"{null_pct}% missing",
                "severity": "Medium",
                "remedy": "Impute with median/mean (numeric) or most-frequent (categorical). Flag non-random nulls for review."
            })

        # Single value
        if n_unique == 1:
            issues.append({
                "col": name,
                "issue": "Single value",
                "detail": "Only one unique value",
                "severity": "High",
                "remedy": "Drop column; provides zero information. Audit data source."
            })

        # Near-constant (numeric)
        if is_numeric and col["stats"]["std"] == 0:
            issues.append({
                "col": name,
                "issue": "Near-constant",
                "detail": "Standard deviation is zero",
                "severity": "Medium",
                "remedy": "Investigate whether column is meaningful; apply variance checks before modelling."
            })

        # Potential outliers (numeric)
        if is_numeric:
            stats = col["stats"]
            iqr = stats["p75"] - stats["p25"]
            if iqr > 0:
                if (stats["max"] - stats["p75"]) > 3 * iqr or (stats["p25"] - stats["min"]) > 3 * iqr:
                    issues.append({
                        "col": name,
                        "issue": "Potential outliers",
                        "detail": "Values beyond 3*IQR from quartiles",
                        "severity": "Medium",
                        "remedy": "Clip to [p1, p99] or apply IQR capping. Confirm whether values are errors or legitimate."
                    })

        # High skew (numeric)
        if is_numeric:
            mean = stats["mean"]
            median = stats["median"]
            if mean and median and mean > 0 and median > 0:
                if mean / median > 2:
                    issues.append({
                        "col": name,
                        "issue": "High right skew",
                        "detail": f"mean/median = {round(mean/median, 2)}",
                        "severity": "Low",
                        "remedy": "Apply log / sqrt / Box-Cox transform before algorithms that assume normality."
                    })
                elif median / mean > 2:
                    issues.append({
                        "col": name,
                        "issue": "High left skew",
                        "detail": f"median/mean = {round(median/mean, 2)}",
                        "severity": "Low",
                        "remedy": "Apply log / sqrt / Box-Cox transform before algorithms that assume normality."
                    })

        # Possible ID/free-text
        if not is_numeric and n_unique / n_rows > 0.9:
            issues.append({
                "col": name,
                "issue": "Possible ID/free-text",
                "detail": f"n_unique/n_rows > 0.9 ({n_unique}/{n_rows})",
                "severity": "Low",
                "remedy": "Exclude from ML features; extract structured sub-fields if meaningful."
            })

        # Mis-typed numeric
        if not is_numeric and n_unique <= 5 and any(kw in name.lower() for kw in ["id", "count", "num", "qty", "amount"]):
            issues.append({
                "col": name,
                "issue": "Mis-typed numeric",
                "detail": f"Non-numeric with {n_unique} uniques, name suggests numeric",
                "severity": "Medium",
                "remedy": "Cast with pd.to_numeric(..., errors='coerce') and inspect introduced nulls."
            })

        # Imbalanced categorical
        if "top_values" in col and col["top_values"]:
            top_pct = col["top_values"][0]["pct"]
            if top_pct > 90:
                issues.append({
                    "col": name,
                    "issue": "Imbalanced categorical",
                    "detail": f"Top value {col['top_values'][0]['value']} at {top_pct}%",
                    "severity": "Medium",
                    "remedy": "Use SMOTE, class-weighted models, or stratified splits. Confirm bias vs. reality."
                })

    return issues