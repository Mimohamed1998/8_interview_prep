# /dq-report — Data Quality Report Generator

## Description
Generates a comprehensive data quality report in Markdown for a specified dataset. The report includes null/missing percentages, dtype info, numeric statistics, and for categorical columns the unique values and their counts.

## Trigger
Invoked when the user runs `/dq-report` or asks for a "data quality report", "DQ report", or "data quality check".

## Arguments
`/dq-report <dataset_path> [output_path]`

- `<dataset_path>` — absolute or relative path to the dataset (CSV, Parquet, Excel, or JSON).
- `[output_path]` — optional path where the `.md` report should be written. Defaults to the same directory as the dataset, named `<dataset_stem>_dq_report.md`.

## Instructions

Follow these steps precisely when this skill is invoked:

### Step 1 — Parse arguments
Extract `dataset_path` and `output_path` from the user's message or the args string.
- If `output_path` is not provided, derive it: same directory as `dataset_path`, filename = `<stem>_dq_report.md`.
- If a relative path is given, resolve it against the current working directory.

### Step 2 — Write and run a Python analysis script

Write the following Python snippet as a **one-shot inline Bash command** (no temp files) and capture its stdout as JSON. Use `python3 -c '...'` or a heredoc. Adjust the loader based on file extension (`.csv` → `pd.read_csv`, `.parquet` → `pd.read_parquet`, `.xlsx`/`.xls` → `pd.read_excel`, `.json` → `pd.read_json`).

```python
import pandas as pd, json, sys, math

path = "<DATASET_PATH>"

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
    sys.exit(f"Unsupported extension: {ext}")

n_rows, n_cols = df.shape
result = {
    "n_rows": n_rows,
    "n_cols": n_cols,
    "columns": []
}

CATEGORICAL_THRESHOLD = 50  # unique values below this → treat as categorical

for col in df.columns:
    series = df[col]
    null_count = int(series.isna().sum())
    null_pct = round(null_count / n_rows * 100, 2) if n_rows else 0
    dtype = str(series.dtype)
    n_unique = int(series.nunique(dropna=True))
    is_numeric = pd.api.types.is_numeric_dtype(series)

    col_info = {
        "name": col,
        "dtype": dtype,
        "null_count": null_count,
        "null_pct": null_pct,
        "n_unique": n_unique,
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

print(json.dumps(result))
```

### Step 3 — Build the Markdown report

Using the JSON output from Step 2, construct a Markdown string with the following sections:

---

```
# Data Quality Report: <filename>

Generated: <today's date>

## Overview

| Metric | Value |
|--------|-------|
| Rows | <n_rows> |
| Columns | <n_cols> |

---

## Column Summary

| Column | dtype | Null Count | Null % | Unique Values |
|--------|-------|-----------|--------|---------------|
| ... one row per column ... |

---

## Column Details

### `<col_name>`
- **dtype:** ...
- **Null count:** ... / <n_rows> (<null_pct>%)
- **Unique values:** ...

#### Numeric Statistics  ← only if numeric
| Stat | Value |
|------|-------|
| Mean | ... |
| Std  | ... |
| Min  | ... |
| 25th pct | ... |
| Median | ... |
| 75th pct | ... |
| Max  | ... |

#### Top Values  ← only if categorical
| Value | Count | % |
|-------|-------|---|
| ...   |  ...  |...|

---
```

Repeat the `### \`col_name\`` block for every column.

### Step 4 — Write the report

Write the full Markdown string to `output_path` using the Write tool. Then tell the user:
- The absolute path of the report
- A one-line summary: how many columns, how many had >5% nulls, how many were treated as categorical
