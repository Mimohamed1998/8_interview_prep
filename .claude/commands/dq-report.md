# /dq-report — Data Quality Report Generator

## Description
Generates a step-by-step data quality Jupyter notebook (`.ipynb`) for a specified dataset. Each analysis step is its own cell — data loading, overview, null analysis, statistics, visualisations, DQ issue detection with remedial actions — ending with a conclusion cell that summarises all findings.

## Trigger
Invoked when the user runs `/dq-report` or asks for a "data quality report", "DQ report", or "data quality check".

## Arguments
`/dq-report <dataset_path> [output_path]`

- `<dataset_path>` — absolute or relative path to the dataset (CSV, Parquet, Excel, or JSON).
- `[output_path]` — optional path where the `.ipynb` notebook should be written. Must end in `.ipynb`. Defaults to the same directory as the dataset, named `<dataset_stem>_dq_report.ipynb`.

## Instructions

Follow these steps precisely when this skill is invoked:

### Step 1 — Parse arguments

Extract `dataset_path` and `output_path` from the user's message or the args string.
- If `output_path` is not provided, derive it: same directory as `dataset_path`, filename = `<stem>_dq_report.ipynb`.
- If a relative path is given, resolve it against the current working directory.
- Always use absolute paths internally.

### Step 2 — Run the analysis script via Bash

Run the following Python snippet as a one-shot inline Bash command and capture its stdout as JSON. Adjust the loader based on file extension (`.csv` → `pd.read_csv`, `.parquet` → `pd.read_parquet`, `.xlsx`/`.xls` → `pd.read_excel`, `.json` → `pd.read_json`).

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

print(json.dumps(result))
```

Store the parsed JSON as `analysis`.

### Step 3 — Detect DQ issues

Using `analysis`, apply these rules to build an `issues` list. Each entry: `{col, issue, detail, severity, remedy}`.

| Issue | Condition | Severity |
|-------|-----------|----------|
| High nulls | `null_pct > 20` | High |
| Moderate nulls | `5 < null_pct ≤ 20` | Medium |
| Single value | `n_unique == 1` | High |
| Near-constant | numeric, `std == 0` | Medium |
| Potential outliers | numeric, `(max - p75) > 3*(p75-p25)` OR `(p25-min) > 3*(p75-p25)` | Medium |
| High right skew | numeric, `mean/median > 2` (both > 0) | Low |
| High left skew | numeric, `median/mean > 2` (both > 0) | Low |
| Possible ID/free-text | non-numeric, `n_unique/n_rows > 0.9` | Low |
| Mis-typed numeric | non-numeric, `n_unique <= 5`, col name contains id/count/num/qty/amount | Medium |
| Imbalanced categorical | top_values present, top value pct > 90 | Medium |

Remedy text per issue:
- **High nulls** — Drop column if low value; otherwise impute with median (numeric) or mode (categorical). Investigate upstream pipeline.
- **Moderate nulls** — Impute with median/mean (numeric) or most-frequent (categorical). Flag non-random nulls for review.
- **Single value** — Drop column; provides zero information. Audit data source.
- **Near-constant** — Investigate whether column is meaningful; apply variance checks before modelling.
- **Potential outliers** — Clip to [p1, p99] or apply IQR capping. Confirm whether values are errors or legitimate.
- **High skew** — Apply log / sqrt / Box-Cox transform before algorithms that assume normality.
- **Possible ID/free-text** — Exclude from ML features; extract structured sub-fields if meaningful.
- **Mis-typed numeric** — Cast with `pd.to_numeric(..., errors='coerce')` and inspect introduced nulls.
- **Imbalanced categorical** — Use SMOTE, class-weighted models, or stratified splits. Confirm bias vs. reality.

### Step 4 — Build the notebook cells

Construct the notebook as a list of cells. Each cell is either a `markdown` cell or a `code` cell. Build the following cells **in order**:

---

#### Cell 1 — Markdown: Title
```
# Data Quality Report: <filename>
**Dataset:** `<dataset_path>`
**Generated:** <today's date>
**Rows:** <n_rows> | **Columns:** <n_cols>
```

---

#### Cell 2 — Code: Imports & Data Loading
Write executable Python that a reader can re-run. Use the actual `dataset_path` value.

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import warnings
warnings.filterwarnings("ignore")

# ── Load dataset ──────────────────────────────────────────────────
DATASET_PATH = "<dataset_path>"

ext = DATASET_PATH.rsplit(".", 1)[-1].lower()
loaders = {"csv": pd.read_csv, "parquet": pd.read_parquet,
           "json": pd.read_json, "xlsx": pd.read_excel, "xls": pd.read_excel}
df = loaders[ext](DATASET_PATH)

print(f"Loaded: {df.shape[0]:,} rows × {df.shape[1]} columns")
df.head()
```

---

#### Cell 3 — Markdown: Step 1 — Dataset Overview

```
## Step 1 — Dataset Overview
High-level shape, column names, and dtypes.
```

#### Cell 4 — Code: Dataset Overview

```python
print(f"Shape: {df.shape}")
print(f"\nColumn dtypes:")
print(df.dtypes.to_string())
```

---

#### Cell 5 — Markdown: Step 2 — Null / Missing Analysis

```
## Step 2 — Null / Missing Analysis
Percentage of missing values per column.
```

#### Cell 6 — Code: Null analysis table + bar chart

Build actual Python using the real column names and null_pct values from `analysis`:

```python
import pandas as pd
import matplotlib.pyplot as plt

null_data = {
    "Column":     [<list of col names>],
    "Null Count": [<list of null_count values>],
    "Null %":     [<list of null_pct values>],
}
null_df = pd.DataFrame(null_data).sort_values("Null %", ascending=False)
display(null_df.style.bar(subset=["Null %"], color="#d65f5f", vmin=0, vmax=100))

# Bar chart
fig, ax = plt.subplots(figsize=(max(8, len(null_df)*0.5), 4))
ax.bar(null_df["Column"], null_df["Null %"], color="#d65f5f", edgecolor="white")
ax.axhline(5,  color="orange", linestyle="--", linewidth=1, label="5% threshold")
ax.axhline(20, color="red",    linestyle="--", linewidth=1, label="20% threshold")
ax.set_ylabel("Missing %")
ax.set_title("Missing Values by Column")
ax.set_xticklabels(null_df["Column"], rotation=45, ha="right")
ax.legend()
plt.tight_layout()
plt.show()
```

---

#### Cell 7 — Markdown: Step 3 — Numeric Statistics

```
## Step 3 — Numeric Statistics
Descriptive statistics for all numeric columns.
```

#### Cell 8 — Code: Numeric statistics

```python
df.describe().T.style.background_gradient(cmap="Blues")
```

---

#### Cell 9 — Markdown: Step 4 — Categorical Distributions

```
## Step 4 — Categorical Distributions
Value counts for low-cardinality (≤ 50 unique values) columns.
```

#### Cell 10 — Code: Categorical bar charts

Generate one subplot per categorical column (those that have `top_values` in `analysis`). Use actual column names and value counts. If no categorical columns exist, print a message instead.

```python
cat_cols = [c for c in df.columns if df[c].nunique() <= 50 and not pd.api.types.is_numeric_dtype(df[c])]

if not cat_cols:
    print("No categorical columns found.")
else:
    fig, axes = plt.subplots(len(cat_cols), 1, figsize=(10, 4 * len(cat_cols)))
    if len(cat_cols) == 1:
        axes = [axes]
    for ax, col in zip(axes, cat_cols):
        vc = df[col].value_counts(dropna=False).head(20)
        ax.barh(vc.index.astype(str), vc.values, color="#4472C4")
        ax.set_title(f"{col} — top values")
        ax.set_xlabel("Count")
        ax.invert_yaxis()
    plt.tight_layout()
    plt.show()
```

---

#### Cell 11 — Markdown: Step 5 — DQ Issue Detection

```
## Step 5 — Data Quality Issue Detection
Automated checks for nulls, outliers, skew, cardinality, and imbalance.
```

#### Cell 12 — Code: DQ issue table

Build a DataFrame from the `issues` list computed in Step 3. Use actual values.

```python
import pandas as pd

issues_data = [
    # {"Column": ..., "Issue": ..., "Detail": ..., "Severity": ...},
    <one dict per issue detected>
]

if not issues_data:
    print("✅ No data quality issues detected.")
else:
    issues_df = pd.DataFrame(issues_data)
    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    issues_df["_order"] = issues_df["Severity"].map(severity_order)
    issues_df = issues_df.sort_values("_order").drop(columns="_order")

    def color_severity(val):
        colors = {"High": "background-color: #f4cccc",
                  "Medium": "background-color: #fff2cc",
                  "Low": "background-color: #cfe2f3"}
        return colors.get(val, "")

    display(issues_df.style.applymap(color_severity, subset=["Severity"]))
```

---

#### Cell 13 — Markdown: Step 6 — Remedial Actions

```
## Step 6 — Remedial Actions
Recommended fixes for each detected issue.
```

#### Cell 14 — Code: Remedial actions table

```python
remedies_data = [
    # {"Column": ..., "Issue": ..., "Severity": ..., "Recommended Action": ...},
    <one dict per issue, using the remedy text from Step 3>
]

if not remedies_data:
    print("✅ No remedial actions required.")
else:
    pd.DataFrame(remedies_data).style.applymap(color_severity, subset=["Severity"])
```

---

#### Cell 15 — Markdown: Conclusion

Build this cell using actual numbers from `analysis` and `issues`:

```markdown
## Conclusion

### Dataset Summary
| Metric | Value |
|--------|-------|
| Total rows | <n_rows> |
| Total columns | <n_cols> |
| Columns with >5% nulls | <count> |
| Columns with >20% nulls | <count> |
| Numeric columns | <count> |
| Categorical columns | <count> |
| Total DQ issues found | <count> |

### Issue Breakdown
| Severity | Count |
|----------|-------|
| 🔴 High | <count> |
| 🟡 Medium | <count> |
| 🔵 Low | <count> |

### Key Findings
<Write 3–5 bullet points calling out the most important findings from the analysis.
 Reference specific column names, percentages, and issue types found.
 Be specific — not generic. E.g.:
 - Column `revenue` has 34.1% missing values and should be imputed or dropped before modelling.
 - Column `category` is highly imbalanced — "Unknown" accounts for 91% of values.>

### Recommended Next Steps
<Write 3–5 prioritised action items, starting with High-severity issues.>
```

---

### Step 5 — Write the notebook file

Construct the final `.ipynb` JSON using nbformat 4. Use the Write tool to save it to `output_path`.

The notebook JSON skeleton:

```json
{
 "nbformat": 4,
 "nbformat_minor": 5,
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.10.0"}
 },
 "cells": [ <cells array> ]
}
```

Each markdown cell:
```json
{"cell_type": "markdown", "id": "<unique-id>", "metadata": {}, "source": ["<line1>\n", "<line2>\n"]}
```

Each code cell:
```json
{"cell_type": "code", "id": "<unique-id>", "metadata": {}, "execution_count": null, "outputs": [], "source": ["<line1>\n", "<line2>\n"]}
```

Use short unique IDs (e.g. `"cell-01"`, `"cell-02"`, …).

Split source strings into a list of lines where each line ends with `\n` except the last.

### Step 6 — Report to the user

After writing the file, tell the user:
- The absolute path of the `.ipynb` notebook
- Total columns, columns with >5% nulls, categorical columns
- DQ issue count broken down by severity (High / Medium / Low)
- Instruct them to open the notebook and run all cells (`Run All`) to see rendered outputs and charts
