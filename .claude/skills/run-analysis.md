# /run-analysis — Analysis & Synthesis Agent

## Description
Reads a specified analysis plan from `docs/2_plan/`, implements every step in a
complete Jupyter notebook (using pandas, statsmodels, linearmodels), generates
McKinsey dark-navy visualizations, executes the notebook end-to-end, validates
all outputs, and finishes with a plain-language synthesis that any non-statistician
can understand. Works for plan files `02` through `07`.

## Trigger
Invoked when the user runs `/run-analysis <plan>`, or asks to "run the analysis",
"implement the plan", "execute the plan", "analyse per the plan", or "build the analysis notebook".

## Arguments
`/run-analysis <plan>`
- `<plan>` — plan number (`02`–`07`), filename (`06_H2_plan.md`), or full path (`docs/2_plan/06_H2_plan.md`).
- If omitted → ask the user: "Which plan file? (02–07 or full path)"

---

## Instructions

Follow every step in order. Do not skip steps. Do not write any files until Step 6.
Steps 6 → 7 → 8 → 9 must all complete before reporting success to the user.

---

### Step 1 — Parse argument and resolve plan file

1. Extract `<plan>` from the user's message or args string.
2. Resolve to an absolute path:
   - If it is a bare number like `06` → map to `docs/2_plan/` using this lookup:
     - `01` → `01_data_gathering_plan.md`
     - `02` → `02_RQ1_plan.md`
     - `03` → `03_RQ2_plan.md`
     - `04` → `04_RQ3_plan.md`
     - `05` → `05_H1_plan.md`
     - `06` → `06_H2_plan.md`
     - `07` → `07_H3_plan.md`
   - If it is a filename → prepend `docs/2_plan/`
   - If it is already a path → use as-is (resolve relative to CWD)
3. Confirm the resolved `.md` file exists (use Bash `ls`). If not found, stop and tell the user.
4. Extract the **plan code** from the filename prefix (e.g., `06_H2_plan.md` → code = `h2`, `02_RQ1_plan.md` → code = `rq1`).
5. Tell the user: "Running analysis for `<filename>` (plan code: `<code>`) …"

---

### Step 2 — Load context

Read both files in parallel:
- `docs/1_requirements/1_research_proposal.md` — for research question and hypothesis context
- The resolved plan file from Step 1

From the research proposal, hold in memory:
- Study title, main RQs, hypotheses (H1/H2/H3)
- Dataset: `data/3_processed_data/master_features/panel_dataset_2020_2023.parquet`
- Key variables: `ai_readiness_score` (IV), `wgi_composite` (Moderator/IV), `sdg_index_score` (DV), `country_group` (Categorical), `country`, `year`, `iso_code`
- Sample: 15–26 countries × 4 years (2020–2023)

From the plan file, extract:
- **Plan title** (first H1 heading)
- **Hypothesis or RQ** being addressed (bold text near the top)
- **Data path** (from the "Data required:" line)
- **Key variables** (from the "Key variables:" line)
- **All steps** (each `## Step N` section): capture heading + full body text
- **Expected output files** (final table)

---

### Step 3 — Introspect the dataset

Run the following Python via Bash and capture the output:

```python
import pandas as pd, json
df = pd.read_parquet("data/3_processed_data/master_features/panel_dataset_2020_2023.parquet")
print(json.dumps({
    "shape": list(df.shape),
    "columns": list(df.columns),
    "dtypes": {c: str(df[c].dtype) for c in df.columns},
    "n_countries": int(df["country"].nunique()),
    "years": sorted(df["year"].unique().tolist()),
    "country_groups": df["country_group"].unique().tolist(),
    "countries": df["country"].unique().tolist(),
    "numeric_summary": df.describe().round(4).to_dict()
}))
```

Store the result as `ds` (dataset metadata). Use it throughout to reference actual column names, value ranges, and country lists.

---

### Step 4 — Determine plan type

Classify the plan using the plan code:
- **RQ plan**: code is `rq1`, `rq2`, or `rq3` → Full analysis pipeline (descriptive → visual → correlation → panel regressions → conclusion)
- **H plan**: code is `h1`, `h2`, or `h3` → Hypothesis test pipeline (extract β1 from corresponding RQ → one-tailed test → effect size → robustness → visualization → reporting)
- **Data plan**: code is `data` → Skip (not in scope for this skill; refer user to `/raw-to-primary`)

For H plans, note the corresponding RQ:
- H1 ↔ RQ1 (`rq1`)
- H2 ↔ RQ2 (`rq2`)
- H3 ↔ RQ3 (`rq3`)

---

### Step 5 — Build the Jupyter notebook cells

Build the notebook as an ordered list of cells. Each cell is either `markdown` or `code`.
Use short sequential IDs: `"cell-01"`, `"cell-02"`, etc.

Follow the structure below. Generate all code with **real column names and values** from `ds`. Never use placeholder strings like `<col>` in code cells.

---

#### BLOCK A — Setup (always first, all plan types)

**Cell A1 — Markdown: Title**
```
# <Plan Title>
**Plan file:** `<plan_filename>`
**Plan code:** `<plan_code>`
**Dataset:** `data/3_processed_data/master_features/panel_dataset_2020_2023.parquet`
**Date:** <today's date>

> <One-sentence plain-English statement of what this analysis is about>
```

**Cell A2 — Code: Imports & McKinsey theme constants**

Write this cell exactly (no placeholders — it is complete):
```python
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

try:
    from linearmodels.panel import PanelOLS, RandomEffects
    from linearmodels.panel.results import compare
    HAS_LINEARMODELS = True
except ImportError:
    HAS_LINEARMODELS = False
    print("⚠️  linearmodels not installed — panel models will use statsmodels workaround")

# ── McKinsey dark-navy style constants ────────────────────────────────────────
BG_DARK        = "#0A1628"
GRID_COLOR     = "#1E3A5F"
TEXT_WHITE     = "#FFFFFF"
TEXT_DARK      = "#0A1628"
C1             = "#4FC3F7"   # sky blue  — 1st series / Developed
C2             = "#4DB6AC"   # teal      — 2nd series / Developing
C3             = "#1A73E8"   # blue      — 3rd series / Lower Governance
C4             = "#FFD600"   # gold      — accent / highlight
C5             = "#FF7043"   # orange    — 5th series

GROUP_COLORS = {
    "Developed":        C1,
    "Developing":       C2,
    "Lower Governance": C3,
}

MCKINSEY_RC = {
    "figure.facecolor": BG_DARK, "figure.figsize": (14, 7), "figure.dpi": 150,
    "axes.facecolor": BG_DARK, "axes.edgecolor": GRID_COLOR,
    "axes.labelcolor": TEXT_WHITE, "axes.titlecolor": TEXT_WHITE,
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlepad": 16,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "axes.spines.bottom": False,
    "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRID_COLOR, "grid.linestyle": "--", "grid.linewidth": 0.6,
    "lines.linewidth": 2.5,
    "xtick.color": TEXT_WHITE, "ytick.color": TEXT_WHITE,
    "xtick.labelsize": 9, "ytick.labelsize": 9,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "legend.facecolor": BG_DARK, "legend.framealpha": 0.0,
    "legend.labelcolor": TEXT_WHITE, "legend.fontsize": 9,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica Neue", "DejaVu Sans"],
    "text.color": TEXT_WHITE,
    "savefig.facecolor": BG_DARK, "savefig.bbox": "tight", "savefig.dpi": 150,
}
plt.rcParams.update(MCKINSEY_RC)

import os
os.makedirs("outputs", exist_ok=True)
print("✅ Setup complete — McKinsey theme loaded")
```

**Cell A3 — Markdown: Data Loading**
```
## Data Loading
Loading the panel dataset and verifying structure.
```

**Cell A4 — Code: Load data**
```python
DATA_PATH = "data/3_processed_data/master_features/panel_dataset_2020_2023.parquet"
df = pd.read_parquet(DATA_PATH)

print(f"Dataset shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"Countries: {df['country'].nunique()} | Years: {sorted(df['year'].unique())} | Groups: {df['country_group'].unique().tolist()}")
print("\nColumn dtypes:")
print(df.dtypes.to_string())
df.head(8)
```

---

#### BLOCK B — Analysis cells (generated per plan type)

Generate one markdown cell + one or more code cells for each `## Step N` section in the plan.

Use the step heading as the markdown cell header. The code cells implement what the step describes.

Apply these **implementation rules** for common step types:

---

##### Rule B1 — Descriptive Statistics steps

When a step says "compute descriptive statistics" or "summary statistics":

```python
# Descriptive statistics for <variable(s)>
desc_cols = [<list of key numeric column names from ds>]

# Overall
overall = df[desc_cols].describe().T.round(3)
overall.columns = ["count","mean","std","min","25%","median","75%","max"]
print("=== Overall Descriptive Statistics ===")
display(overall)

# By country group
by_group = df.groupby("country_group")[desc_cols].describe().round(3)
print("\n=== By Country Group ===")
display(by_group)

# By year
by_year = df.groupby("year")[desc_cols].mean().round(3)
print("\n=== Year-wise Means ===")
display(by_year)

# Save
prefix = "<plan_code>"
overall.to_csv(f"outputs/{prefix}_descriptive_stats.csv")
print(f"\n✅ Saved: outputs/{prefix}_descriptive_stats.csv")
```

---

##### Rule B2 — Scatter plot with regression line (McKinsey style)

When a step calls for a scatter plot of IV vs DV, color-coded by group:

```python
x_col = "<IV column>"   # e.g. "ai_readiness_score" or "wgi_composite"
y_col = "sdg_index_score"
prefix = "<plan_code>"

fig, ax = plt.subplots()
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_DARK)
for s in ax.spines.values(): s.set_visible(False)

for group, color in GROUP_COLORS.items():
    mask = df["country_group"] == group
    ax.scatter(df.loc[mask, x_col], df.loc[mask, y_col],
               color=color, s=60, alpha=0.85, zorder=5, label=group)

# Label each country (use mean position across years)
country_means = df.groupby("country")[[x_col, y_col]].mean()
for country, row in country_means.iterrows():
    ax.text(row[x_col] + 0.3, row[y_col], country[:3].upper(),
            color=TEXT_WHITE, fontsize=6.5, va="center", alpha=0.8)

# OLS trend line
x_vals = df[x_col].dropna()
y_vals = df.loc[x_vals.index, y_col].dropna()
common_idx = x_vals.index.intersection(y_vals.index)
x_v, y_v = x_vals[common_idx].values, y_vals[common_idx].values
m, b = np.polyfit(x_v, y_v, 1)
x_line = np.linspace(x_v.min(), x_v.max(), 100)
ax.plot(x_line, m * x_line + b, color=TEXT_WHITE, linewidth=1.5,
        linestyle="--", alpha=0.7, label=f"OLS trend (slope={m:.2f})")

# CI band (95%)
from scipy import stats as _st
n = len(x_v)
x_mean = x_v.mean()
se = np.sqrt(sum((y_v - (m*x_v+b))**2)/(n-2)) * np.sqrt(1/n + (x_line-x_mean)**2/sum((x_v-x_mean)**2))
t_crit = _st.t.ppf(0.975, n-2)
ax.fill_between(x_line, m*x_line+b - t_crit*se, m*x_line+b + t_crit*se,
                color=TEXT_WHITE, alpha=0.08)

ax.set_xlabel(x_col.replace("_", " ").title(), color=TEXT_WHITE, fontsize=10)
ax.set_ylabel(y_col.replace("_", " ").title(), color=TEXT_WHITE, fontsize=10)
ax.set_title(f"{x_col.replace('_',' ').title()} vs SDG Index Score\n(n={len(df)}, colour = country group)",
             fontweight="bold", color=TEXT_WHITE)
ax.legend(loc="upper left", framealpha=0.0)
plt.tight_layout()
plt.savefig(f"outputs/{prefix}_scatter_plot.png", bbox_inches="tight", facecolor=BG_DARK)
plt.show()
print(f"✅ Saved: outputs/{prefix}_scatter_plot.png")
```

---

##### Rule B3 — Bar chart (mean by group, with error bars)

When a step calls for a bar chart of group means:

```python
metric_col = "sdg_index_score"   # or whichever column the step specifies
prefix = "<plan_code>"

group_stats = df.groupby("country_group")[metric_col].agg(["mean","sem"]).reset_index()
group_stats.columns = ["group","mean","sem"]
order = ["Developed", "Developing", "Lower Governance"]
group_stats = group_stats.set_index("group").reindex(order).reset_index()

fig, ax = plt.subplots(figsize=(9, 6))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_DARK)
for s in ax.spines.values(): s.set_visible(False)

colors = [GROUP_COLORS[g] for g in group_stats["group"]]
bars = ax.bar(group_stats["group"], group_stats["mean"],
              color=colors, width=0.55, zorder=5, alpha=0.9)
ax.errorbar(group_stats["group"], group_stats["mean"], yerr=group_stats["sem"],
            fmt="none", color=TEXT_WHITE, capsize=6, lw=1.5, zorder=6)

for bar, val in zip(bars, group_stats["mean"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f"{val:.1f}", ha="center", va="bottom", color=TEXT_WHITE,
            fontweight="bold", fontsize=11)

ax.set_ylabel(metric_col.replace("_"," ").title(), color=TEXT_WHITE, fontsize=10)
ax.set_title(f"Mean {metric_col.replace('_',' ').title()} by Country Group\n(error bars = ±1 SE)",
             fontweight="bold", color=TEXT_WHITE)
ax.set_ylim(0, group_stats["mean"].max() * 1.2)
ax.tick_params(axis="x", labelsize=11, colors=TEXT_WHITE)
plt.tight_layout()
plt.savefig(f"outputs/{prefix}_group_bar_chart.png", bbox_inches="tight", facecolor=BG_DARK)
plt.show()
print(f"✅ Saved: outputs/{prefix}_group_bar_chart.png")
```

---

##### Rule B4 — Line plot over time (by country group)

When a step calls for a time-series line plot:

```python
metric_col = "<column to plot>"
prefix = "<plan_code>"

trend = df.groupby(["year","country_group"])[metric_col].mean().reset_index()

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_DARK)
for s in ax.spines.values(): s.set_visible(False)

for group, color in GROUP_COLORS.items():
    mask = trend["country_group"] == group
    sub = trend[mask]
    ax.plot(sub["year"], sub[metric_col], color=color, linewidth=2.5,
            marker="o", markersize=7, label=group, zorder=5)
    # End-of-line label
    last = sub.iloc[-1]
    ax.text(last["year"] + 0.08, last[metric_col],
            f"{last[metric_col]:.1f}", color=color, fontweight="bold",
            fontsize=9, va="center", ha="left")

ax.set_xlim(df["year"].min() - 0.2, df["year"].max() + 0.8)
ax.set_xticks(sorted(df["year"].unique()))
ax.set_xlabel("Year", color=TEXT_WHITE, fontsize=10)
ax.set_ylabel(metric_col.replace("_"," ").title(), color=TEXT_WHITE, fontsize=10)
ax.set_title(f"{metric_col.replace('_',' ').title()} Trend by Country Group (2020–2023)",
             fontweight="bold", color=TEXT_WHITE)
ax.legend(loc="upper left", framealpha=0.0)
plt.tight_layout()
plt.savefig(f"outputs/{prefix}_line_trend.png", bbox_inches="tight", facecolor=BG_DARK)
plt.show()
print(f"✅ Saved: outputs/{prefix}_line_trend.png")
```

---

##### Rule B5 — Box plot (distribution by group)

When a step calls for box plots:

```python
metric_col = "<column>"
prefix = "<plan_code>"
groups = ["Developed", "Developing", "Lower Governance"]

fig, ax = plt.subplots(figsize=(10, 6))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_DARK)
for s in ax.spines.values(): s.set_visible(False)

data_per_group = [df.loc[df["country_group"]==g, metric_col].dropna().values for g in groups]
bp = ax.boxplot(data_per_group, labels=groups, patch_artist=True,
                medianprops=dict(color=C4, linewidth=2),
                whiskerprops=dict(color=TEXT_WHITE),
                capprops=dict(color=TEXT_WHITE),
                flierprops=dict(marker="o", color=C4, markersize=5))

for patch, color in zip(bp["boxes"], [C1, C2, C3]):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)

ax.set_ylabel(metric_col.replace("_"," ").title(), color=TEXT_WHITE, fontsize=10)
ax.set_title(f"Distribution of {metric_col.replace('_',' ').title()} by Country Group",
             fontweight="bold", color=TEXT_WHITE)
ax.tick_params(axis="x", labelsize=11, colors=TEXT_WHITE)
plt.tight_layout()
plt.savefig(f"outputs/{prefix}_box_plot.png", bbox_inches="tight", facecolor=BG_DARK)
plt.show()
print(f"✅ Saved: outputs/{prefix}_box_plot.png")
```

---

##### Rule B6 — Heatmap (countries × years)

When a step calls for a heatmap of countries by years:

```python
x_col = "<column>"    # e.g. "wgi_composite"
prefix = "<plan_code>"

pivot = df.pivot_table(index="country", columns="year", values=x_col, aggfunc="mean")
pivot = pivot.sort_values(pivot.columns[-1], ascending=False)

fig, ax = plt.subplots(figsize=(10, 9))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_DARK)
for s in ax.spines.values(): s.set_visible(False)

import matplotlib.colors as mcolors
cmap = mcolors.LinearSegmentedColormap.from_list("mckinsey", [BG_DARK, C1])
im = ax.imshow(pivot.values, cmap=cmap, aspect="auto")

ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, color=TEXT_WHITE)
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index, color=TEXT_WHITE, fontsize=9)

for i in range(len(pivot.index)):
    for j in range(len(pivot.columns)):
        val = pivot.values[i, j]
        if not np.isnan(val):
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    color=TEXT_WHITE if val < pivot.values.max()*0.6 else TEXT_DARK,
                    fontsize=7.5, fontweight="bold")

cbar = plt.colorbar(im, ax=ax, shrink=0.6)
cbar.ax.yaxis.set_tick_params(color=TEXT_WHITE)
plt.setp(cbar.ax.yaxis.get_ticklabels(), color=TEXT_WHITE)

ax.set_title(f"{x_col.replace('_',' ').title()} Heatmap — Countries × Years",
             fontweight="bold", color=TEXT_WHITE)
plt.tight_layout()
plt.savefig(f"outputs/{prefix}_heatmap.png", bbox_inches="tight", facecolor=BG_DARK)
plt.show()
print(f"✅ Saved: outputs/{prefix}_heatmap.png")
```

---

##### Rule B7 — Pearson / Spearman correlation

When a step asks for correlation analysis:

```python
from scipy.stats import pearsonr, spearmanr

x_col = "<IV column>"
y_col = "sdg_index_score"
prefix = "<plan_code>"

# Pooled
valid = df[[x_col, y_col]].dropna()
r_p, p_p = pearsonr(valid[x_col], valid[y_col])
r_s, p_s = spearmanr(valid[x_col], valid[y_col])
n = len(valid)

# 95% CI for Pearson using Fisher z
z = np.arctanh(r_p)
se_z = 1 / np.sqrt(n - 3)
ci_low  = np.tanh(z - 1.96 * se_z)
ci_high = np.tanh(z + 1.96 * se_z)

corr_results = {
    "Subset": ["Pooled (all)"],
    "N": [n],
    "Pearson r": [round(r_p, 4)],
    "p-value (Pearson)": [round(p_p, 4)],
    "95% CI lower": [round(ci_low, 4)],
    "95% CI upper": [round(ci_high, 4)],
    "Spearman rho": [round(r_s, 4)],
    "p-value (Spearman)": [round(p_s, 4)],
}

# Within-group correlations
for group in ["Developed", "Developing", "Lower Governance"]:
    sub = df.loc[df["country_group"] == group, [x_col, y_col]].dropna()
    if len(sub) > 3:
        rg, pg = pearsonr(sub[x_col], sub[y_col])
        corr_results["Subset"].append(group)
        corr_results["N"].append(len(sub))
        corr_results["Pearson r"].append(round(rg, 4))
        corr_results["p-value (Pearson)"].append(round(pg, 4))
        zg = np.arctanh(rg)
        cil = np.tanh(zg - 1.96/np.sqrt(len(sub)-3))
        ciu = np.tanh(zg + 1.96/np.sqrt(len(sub)-3))
        corr_results["95% CI lower"].append(round(cil, 4))
        corr_results["95% CI upper"].append(round(ciu, 4))
        rs_g, ps_g = spearmanr(sub[x_col], sub[y_col])
        corr_results["Spearman rho"].append(round(rs_g, 4))
        corr_results["p-value (Spearman)"].append(round(ps_g, 4))

corr_df = pd.DataFrame(corr_results)
print(f"=== Correlation: {x_col} vs {y_col} ===")
display(corr_df)

corr_df.to_csv(f"outputs/{prefix}_correlation_results.csv", index=False)
print(f"✅ Saved: outputs/{prefix}_correlation_results.csv")
```

---

##### Rule B8 — Panel regressions (Pooled OLS + FE + RE + Hausman)

When a step asks for Pooled OLS, Fixed Effects, Random Effects, or Hausman test:

```python
x_col = "<IV column>"
y_col = "sdg_index_score"
prefix = "<plan_code>"

# ── Prepare panel index ──────────────────────────────────────────────
df_panel = df[[y_col, x_col, "country", "year"]].dropna().copy()
df_panel = df_panel.set_index(["country", "year"])

# ── 1. Pooled OLS ────────────────────────────────────────────────────
X_ols = sm.add_constant(df_panel[x_col])
ols_res = sm.OLS(df_panel[y_col], X_ols).fit(cov_type="HC3")
print("=== Pooled OLS ===")
print(ols_res.summary2().tables[1])
print(f"R²: {ols_res.rsquared:.4f}")

results_table = [{
    "Model": "Pooled OLS",
    "β1 (IV)": round(float(ols_res.params[x_col]), 4),
    "SE": round(float(ols_res.bse[x_col]), 4),
    "t-stat": round(float(ols_res.tvalues[x_col]), 4),
    "p-value (2-tail)": round(float(ols_res.pvalues[x_col]), 4),
    "CI lower": round(float(ols_res.conf_int().loc[x_col, 0]), 4),
    "CI upper": round(float(ols_res.conf_int().loc[x_col, 1]), 4),
    "R²": round(ols_res.rsquared, 4),
}]

if HAS_LINEARMODELS:
    # ── 2. Fixed Effects (Two-Way) ────────────────────────────────────
    from linearmodels.panel import PanelOLS
    fe_mod = PanelOLS(df_panel[y_col], df_panel[[x_col]],
                      entity_effects=True, time_effects=True)
    fe_res = fe_mod.fit(cov_type="clustered", cluster_entity=True)
    print("\n=== Fixed Effects (Two-Way, Clustered SE) ===")
    print(fe_res.summary.tables[1])

    results_table.append({
        "Model": "Fixed Effects (Two-Way)",
        "β1 (IV)": round(float(fe_res.params[x_col]), 4),
        "SE": round(float(fe_res.std_errors[x_col]), 4),
        "t-stat": round(float(fe_res.tstats[x_col]), 4),
        "p-value (2-tail)": round(float(fe_res.pvalues[x_col]), 4),
        "CI lower": round(float(fe_res.conf_int().loc[x_col, "lower"]), 4),
        "CI upper": round(float(fe_res.conf_int().loc[x_col, "upper"]), 4),
        "R²": round(float(fe_res.rsquared), 4),
    })

    # ── 3. Random Effects ─────────────────────────────────────────────
    from linearmodels.panel import RandomEffects
    re_mod = RandomEffects(df_panel[y_col], sm.add_constant(df_panel[x_col]))
    re_res = re_mod.fit(cov_type="robust")
    print("\n=== Random Effects ===")
    print(re_res.summary.tables[1])

    results_table.append({
        "Model": "Random Effects",
        "β1 (IV)": round(float(re_res.params[x_col]), 4),
        "SE": round(float(re_res.std_errors[x_col]), 4),
        "t-stat": round(float(re_res.tstats[x_col]), 4),
        "p-value (2-tail)": round(float(re_res.pvalues[x_col]), 4),
        "CI lower": round(float(re_res.conf_int().loc[x_col, "lower"]), 4),
        "CI upper": round(float(re_res.conf_int().loc[x_col, "upper"]), 4),
        "R²": round(float(re_res.rsquared), 4),
    })

    # ── 4. Hausman test ───────────────────────────────────────────────
    b_fe = fe_res.params
    b_re = re_res.params.drop("const", errors="ignore")
    common = b_fe.index.intersection(b_re.index)
    diff = (b_fe[common] - b_re[common]).values
    V_fe = fe_res.cov.values
    V_re = re_res.cov.loc[common, common].values
    V_diff = V_fe - V_re
    try:
        chi2 = float(diff @ np.linalg.inv(V_diff) @ diff)
        df_h = len(common)
        from scipy.stats import chi2 as chi2_dist
        p_hausman = 1 - chi2_dist.cdf(chi2, df_h)
        print(f"\n=== Hausman Test ===")
        print(f"Chi² = {chi2:.4f}, df = {df_h}, p = {p_hausman:.4f}")
        hausman_decision = "Fixed Effects preferred (p < 0.05)" if p_hausman < 0.05 else "Random Effects preferred (p ≥ 0.05)"
        print(f"Decision: {hausman_decision}")
        selected_model = "Fixed Effects" if p_hausman < 0.05 else "Random Effects"
        selected_res = fe_res if p_hausman < 0.05 else re_res
    except np.linalg.LinAlgError:
        print("Hausman test: matrix not invertible — defaulting to Fixed Effects")
        selected_model, selected_res = "Fixed Effects", fe_res
        p_hausman = None

reg_df = pd.DataFrame(results_table)
display(reg_df)
reg_df.to_csv(f"outputs/{prefix}_regression_results.csv", index=False)
print(f"✅ Saved: outputs/{prefix}_regression_results.csv")
```

---

##### Rule B9 — Coefficient plot (β1 across models, McKinsey style)

When a step calls for a coefficient plot:

```python
prefix = "<plan_code>"
reg_df_plot = reg_df.copy()  # use reg_df from the regression step

fig, ax = plt.subplots(figsize=(10, 5))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_DARK)
for s in ax.spines.values(): s.set_visible(False)

y_pos = range(len(reg_df_plot))
ax.axvline(0, color=TEXT_WHITE, linewidth=1, linestyle="-", alpha=0.4, zorder=3)

for i, row in reg_df_plot.iterrows():
    color = C4 if "Selected" in row["Model"] else C1
    ax.plot([row["CI lower"], row["CI upper"]], [i, i],
            color=color, linewidth=3, solid_capstyle="round", zorder=4, alpha=0.8)
    ax.scatter(row["β1 (IV)"], i, color=color, s=90, zorder=5)
    ax.text(row["CI upper"] + 0.01, i, f"β={row['β1 (IV)']:.3f} (p={row['p-value (2-tail)']:.3f})",
            color=TEXT_WHITE, fontsize=8, va="center")

ax.set_yticks(list(y_pos))
ax.set_yticklabels(reg_df_plot["Model"], color=TEXT_WHITE, fontsize=9)
ax.set_xlabel("Coefficient (β₁)", color=TEXT_WHITE, fontsize=10)
ax.set_title("Coefficient Plot — β₁ Across Models (95% CI)\nLine = confidence interval, dot = point estimate",
             fontweight="bold", color=TEXT_WHITE)
plt.tight_layout()
plt.savefig(f"outputs/{prefix}_coefficient_plot.png", bbox_inches="tight", facecolor=BG_DARK)
plt.show()
print(f"✅ Saved: outputs/{prefix}_coefficient_plot.png")
```

---

##### Rule B10 — One-tailed hypothesis test (H plans only)

When a step requires a one-tailed t-test on β1:

```python
x_col = "<IV column>"
y_col = "sdg_index_score"
prefix = "<plan_code>"
hypothesis_name = "<H1|H2|H3>"

# Use the selected regression result (FE or RE based on Hausman)
beta1 = float(selected_res.params[x_col])
se    = float(selected_res.std_errors[x_col])
n_obs = int(selected_res.nobs)
df_deg = n_obs - 2

# One-tailed test (H: β1 > 0)
t_stat = beta1 / se
from scipy.stats import t as t_dist
p_onetail = t_dist.sf(t_stat, df=df_deg)   # P(T > t)
ci_lower_bound = beta1 - 1.645 * se        # 95% one-tailed lower bound

print(f"=== {hypothesis_name} Hypothesis Test (One-Tailed) ===")
print(f"β₁ = {beta1:.4f}")
print(f"SE = {se:.4f}")
print(f"t-statistic = {t_stat:.4f}")
print(f"p-value (one-tailed) = {p_onetail:.4f}")
print(f"95% one-tailed CI lower bound: {ci_lower_bound:.4f}")
print()

if beta1 > 0 and p_onetail < 0.05:
    decision = f"✅ REJECT H0 — {hypothesis_name} SUPPORTED (β₁ > 0, p < 0.05 one-tailed)"
else:
    decision = f"❌ FAIL TO REJECT H0 — {hypothesis_name} NOT SUPPORTED"
print(decision)

# Effect sizes
r_squared = float(selected_res.rsquared)
cohens_f2 = r_squared / (1 - r_squared) if r_squared < 1 else float("inf")

# Standardized beta (z-score both variables)
valid = df[[x_col, y_col]].dropna()
x_z = (valid[x_col] - valid[x_col].mean()) / valid[x_col].std()
y_z = (valid[y_col] - valid[y_col].mean()) / valid[y_col].std()
std_beta = float(sm.OLS(y_z, sm.add_constant(x_z)).fit().params[x_col])

print(f"\n=== Effect Sizes ===")
print(f"R² (model): {r_squared:.4f}")
print(f"Cohen's f²: {cohens_f2:.4f} ({('small' if cohens_f2<0.15 else 'medium' if cohens_f2<0.35 else 'large')} effect)")
print(f"Standardized β₁: {std_beta:.4f}")

# Save summary
hyp_summary = pd.DataFrame([{
    "Hypothesis": hypothesis_name,
    "β₁": round(beta1, 4), "SE": round(se, 4),
    "t-stat (one-tail)": round(t_stat, 4),
    "p-value (one-tail)": round(p_onetail, 4),
    "95% CI lower": round(ci_lower_bound, 4),
    "R²": round(r_squared, 4),
    "Cohen's f²": round(cohens_f2, 4),
    "Std. β₁": round(std_beta, 4),
    "Decision": decision
}])
display(hyp_summary)
hyp_summary.to_csv(f"outputs/{prefix}_hypothesis_test_table.csv", index=False)
print(f"✅ Saved: outputs/{prefix}_hypothesis_test_table.csv")
```

---

##### Rule B11 — ANOVA / Kruskal-Wallis between-group test

When a step calls for ANOVA or Kruskal-Wallis:

```python
from scipy.stats import shapiro, f_oneway, kruskal, mannwhitneyu
from itertools import combinations
prefix = "<plan_code>"
metric_col = "sdg_index_score"

groups_data = {g: df.loc[df["country_group"]==g, metric_col].dropna().values
               for g in ["Developed", "Developing", "Lower Governance"]}

# Check normality per group
print("=== Shapiro-Wilk Normality Tests ===")
all_normal = True
for g, data in groups_data.items():
    stat, p = shapiro(data)
    print(f"{g}: W={stat:.4f}, p={p:.4f} {'✅ Normal' if p>=0.05 else '⚠️ Non-normal'}")
    if p < 0.05:
        all_normal = False

print(f"\nUsing: {'ANOVA' if all_normal else 'Kruskal-Wallis (non-parametric)'}")

if all_normal:
    stat, p_val = f_oneway(*groups_data.values())
    test_name = "ANOVA F"
else:
    stat, p_val = kruskal(*groups_data.values())
    test_name = "Kruskal-Wallis H"

print(f"\n{test_name}-statistic = {stat:.4f}, p = {p_val:.4f}")

if p_val < 0.05:
    print("Significant group differences found → running post-hoc pairwise tests")
    group_names = list(groups_data.keys())
    pairs = list(combinations(group_names, 2))
    bonferroni_alpha = 0.05 / len(pairs)
    print(f"Bonferroni corrected α = {bonferroni_alpha:.4f}")
    for g1, g2 in pairs:
        u, p_mw = mannwhitneyu(groups_data[g1], groups_data[g2], alternative="two-sided")
        sig = "✅ Significant" if p_mw < bonferroni_alpha else "—"
        print(f"  {g1} vs {g2}: U={u:.1f}, p={p_mw:.4f} {sig}")
else:
    print("No significant group differences detected (p ≥ 0.05)")

# Group means table
group_means = df.groupby("country_group")[metric_col].agg(["mean","std","count"]).round(3)
display(group_means)
group_means.to_csv(f"outputs/{prefix}_group_comparison.csv")
print(f"✅ Saved: outputs/{prefix}_group_comparison.csv")
```

---

##### Rule B12 — Robustness checks (Cook's Distance + year-by-year)

When a step calls for robustness checks:

```python
x_col = "<IV column>"
y_col = "sdg_index_score"
prefix = "<plan_code>"

# ── Cook's Distance ───────────────────────────────────────────────────
valid = df[[x_col, y_col, "country", "year"]].dropna()
X_rob = sm.add_constant(valid[x_col])
rob_res = sm.OLS(valid[y_col], X_rob).fit()
influence = rob_res.get_influence()
cooks_d = influence.cooks_distance[0]
threshold = 4 / len(valid)
n_outliers = (cooks_d > threshold).sum()
print(f"Cook's D threshold (4/n = 4/{len(valid)}): {threshold:.4f}")
print(f"Observations with Cook's D > threshold: {n_outliers}")

outlier_idx = np.where(cooks_d > threshold)[0]
if len(outlier_idx) > 0:
    print("Influential observations:")
    for idx in outlier_idx:
        row = valid.iloc[idx]
        print(f"  {row['country']} {row['year']}: Cook's D = {cooks_d[idx]:.4f}")

    # Re-run without outliers
    valid_clean = valid.drop(valid.index[outlier_idx])
    X_clean = sm.add_constant(valid_clean[x_col])
    res_clean = sm.OLS(valid_clean[y_col], X_clean).fit(cov_type="HC3")
    print(f"\nModel without outliers: β₁ = {res_clean.params[x_col]:.4f}, p = {res_clean.pvalues[x_col]:.4f}")
    print(f"Original model:         β₁ = {rob_res.params[x_col]:.4f}, p = {rob_res.pvalues[x_col]:.4f}")

# ── Year-by-year OLS ─────────────────────────────────────────────────
print("\n=== Year-by-Year Coefficients ===")
yr_results = []
for yr in sorted(df["year"].unique()):
    sub = df.loc[df["year"]==yr, [x_col, y_col]].dropna()
    if len(sub) < 4:
        continue
    Xy = sm.add_constant(sub[x_col])
    ry = sm.OLS(sub[y_col], Xy).fit()
    yr_results.append({
        "Year": yr, "N": len(sub),
        "β₁": round(float(ry.params[x_col]), 4),
        "SE": round(float(ry.bse[x_col]), 4),
        "p-value": round(float(ry.pvalues[x_col]), 4),
        "R²": round(ry.rsquared, 4),
    })
yr_df = pd.DataFrame(yr_results)
display(yr_df)
yr_df.to_csv(f"outputs/{prefix}_robustness_checks.csv", index=False)
print(f"✅ Saved: outputs/{prefix}_robustness_checks.csv")
```

---

#### BLOCK C — Synthesis cell (always last, all plan types)

**Cell C1 — Markdown: Plain-Language Synthesis**

Generate this cell with **actual numbers filled in** from the analysis cells above. This is not a template — write the real values obtained during analysis. Structure it as follows:

```
## 📊 Plain-Language Synthesis
> *Written for readers who are not statisticians*

---

### What did we study?
<One paragraph: what question were we trying to answer, what data did we use, and why does it matter. No jargon. Use analogies if helpful.>

---

### What did we find?

#### Finding 1 — <Short title, e.g. "Countries with better AI readiness score higher on sustainability">
<2–3 sentences: describe the main finding in everyday language. Include the key number (β₁ = X or correlation r = X) but explain what it means: "In practical terms, for every 10-point increase in AI readiness, a country's sustainability score improved by about X points.">

#### Finding 2 — <Title>
<2–3 sentences on the second key finding (e.g., group differences, trend over time).>

#### Finding 3 — <Title, if applicable>
<Optional third finding.>

---

### How confident are we?

| What we measured | Result | Confidence |
|-----------------|--------|------------|
| <Main relationship> | <β or r value> | <Significant / Not significant> |
| <Group difference> | <p-value or F-stat> | <Strong / Moderate / Weak> |
| <Effect size> | <Cohen's f² or r²> | <Small / Medium / Large effect> |

> **Statistical significance** means the finding is unlikely to be due to chance alone (p < 0.05).
> **Effect size** tells us whether the finding is practically meaningful, not just statistically detectable.

---

### What are the limitations?

- **Observational data:** We can show that <IV> is associated with <DV>, but we cannot prove that one causes the other. Both could be driven by a third factor (e.g., overall national wealth).
- **Sample size:** With <N> country-year observations across <n_countries> countries, our results are directional indicators rather than definitive proof.
- **Time span:** Four years (2020–2023) is a short window. Longer data would give more reliable results.

---

### In plain English: <Summarise the single most important takeaway in one sentence.>
```

**Cell C2 — Code: Export synthesis as markdown file**
```python
import datetime
synthesis_text = """<Copy the full markdown from Cell C1 here as a Python string>"""
with open(f"outputs/{prefix}_synthesis.md", "w") as f:
    f.write(synthesis_text)
print(f"✅ Saved: outputs/{prefix}_synthesis.md")
```

---

### Step 6 — Write the notebook file

1. Create the destination directory:
   ```bash
   mkdir -p pipelines/eda_research_proposals
   ```
2. Construct the final `.ipynb` JSON using nbformat 4:
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
   - Markdown cells: `{"cell_type": "markdown", "id": "cell-01", "metadata": {}, "source": ["line1\n", "line2\n"]}`
   - Code cells: `{"cell_type": "code", "id": "cell-02", "metadata": {}, "execution_count": null, "outputs": [], "source": ["line1\n", "line2\n"]}`
   - Split source into a list of strings where every line (except the last) ends with `\n`.
3. Write the notebook to: `pipelines/eda_research_proposals/<plan_code>_analysis.ipynb`
   Use the Write tool.
4. Tell the user: "📓 Notebook written — now executing …"

---

### Step 7 — Execute the notebook

Run the notebook end-to-end using `jupyter nbconvert` from the project virtual environment.
The executed copy overwrites the source file so outputs are embedded.

```bash
.venv/bin/jupyter nbconvert \
  --to notebook \
  --execute \
  --inplace \
  --ExecutePreprocessor.timeout=300 \
  --ExecutePreprocessor.kernel_name=python3 \
  pipelines/eda_research_proposals/<plan_code>_analysis.ipynb \
  2>&1
```

- `--execute` — runs every cell in order.
- `--inplace` — writes the executed outputs back into the same `.ipynb` file (all cell outputs, figures, print statements become part of the notebook).
- `--ExecutePreprocessor.timeout=300` — allows up to 5 minutes total execution time.

**On error:** If nbconvert exits with a non-zero code, capture stderr, find the cell that failed (look for `CellExecutionError` or a traceback), report it to the user with the cell number and error message, then stop. Do **not** proceed to Step 8.

**On success:** Tell the user: "✅ Notebook executed successfully — validating outputs …"

---

### Step 8 — Validate results

After execution, run the following checks using Bash. Report a ✅ or ❌ for each item.

#### 8a — Notebook executed cleanly (no error outputs)

```bash
.venv/bin/python - <<'EOF'
import json, sys
with open("pipelines/eda_research_proposals/<plan_code>_analysis.ipynb") as f:
    nb = json.load(f)
errors = []
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    for out in cell.get("outputs", []):
        if out.get("output_type") == "error":
            errors.append(f"Cell {i+1} — {out['ename']}: {out['evalue'][:120]}")
if errors:
    print("ERRORS FOUND:")
    for e in errors: print(" ", e)
    sys.exit(1)
else:
    print(f"OK — {len(nb['cells'])} cells, 0 errors")
EOF
```

#### 8b — All expected output files exist

Check that every `.csv` and `.png` listed in the plan's "Expected Output Files" table was actually written to `outputs/`. Use:

```bash
ls outputs/<plan_code>_*.csv outputs/<plan_code>_*.png 2>&1
```

For each missing file, report: `❌ Missing: outputs/<filename>`

#### 8c — Key statistical sanity checks

Run a short Python snippet to verify the regression results make statistical sense. Adjust column names per plan type:

```bash
.venv/bin/python - <<'EOF'
import pandas as pd, sys

prefix = "<plan_code>"
issues = []

# Check regression results CSV
try:
    reg = pd.read_csv(f"outputs/{prefix}_regression_results.csv")
    if reg.empty:
        issues.append("regression_results.csv is empty")
    else:
        # β1 must be numeric and non-null
        b1 = reg["β1 (IV)"].dropna()
        if len(b1) == 0:
            issues.append("β1 column is entirely null")
        else:
            print(f"β1 range: [{b1.min():.4f}, {b1.max():.4f}]")

        # R² must be between 0 and 1
        r2 = reg["R²"].dropna()
        if (r2 < 0).any() or (r2 > 1).any():
            issues.append(f"R² out of range [0,1]: {r2.tolist()}")
        else:
            print(f"R² range: [{r2.min():.4f}, {r2.max():.4f}] ✅")
except FileNotFoundError:
    issues.append(f"outputs/{prefix}_regression_results.csv not found")

# Check descriptive stats CSV
try:
    desc = pd.read_csv(f"outputs/{prefix}_descriptive_stats.csv")
    print(f"Descriptive stats: {desc.shape[0]} rows ✅")
except FileNotFoundError:
    issues.append(f"outputs/{prefix}_descriptive_stats.csv not found")

# Check synthesis markdown
try:
    with open(f"outputs/{prefix}_synthesis.md") as f:
        synth = f.read()
    word_count = len(synth.split())
    if word_count < 80:
        issues.append(f"Synthesis too short ({word_count} words — expected ≥ 80)")
    else:
        print(f"Synthesis: {word_count} words ✅")
except FileNotFoundError:
    issues.append(f"outputs/{prefix}_synthesis.md not found")

if issues:
    print("\n⚠️  Validation issues:")
    for iss in issues: print(f"  ❌ {iss}")
    sys.exit(1)
else:
    print("\n✅ All sanity checks passed")
EOF
```

#### 8d — Report validation summary

Present a table:

```
### Validation Results

| Check | Status | Detail |
|-------|--------|--------|
| Notebook executed cleanly | ✅ / ❌ | N cells, 0 errors / Error in cell X |
| All output files present  | ✅ / ❌ | N files found / Missing: ... |
| β₁ range reasonable       | ✅ / ❌ | range [x, y] |
| R² in [0, 1]              | ✅ / ❌ | range [x, y] |
| Synthesis written          | ✅ / ❌ | N words |
```

If any check is ❌, describe what went wrong and what the user should fix before re-running.

---

### Step 9 — Report to user

After all validation checks pass, present the final summary:

```
## ✅ Analysis Complete

**Plan:** `<plan_filename>` — <plan title>
**Notebook:** `pipelines/eda_research_proposals/<plan_code>_analysis.ipynb`
**Status:** Executed & validated

### What was run
| Section | Status |
|---------|--------|
| Setup — imports, McKinsey theme, data load | ✅ |
<one row per ## Step N from the plan — all ✅>
| Plain-language synthesis | ✅ |

### Output files
| File | Type |
|------|------|
<one row per file in outputs/<plan_code>_* — with short description>

### Key findings (from synthesis)
<3 bullet points summarising the most important statistical results in plain language>

**Next step:** Read `outputs/<plan_code>_synthesis.md` for the full plain-language report.
After completing all RQ/H plans, run `/eda-synthesis` to generate the executive-level cross-plan summary.
```

---

## Code Quality Rules (apply to every code cell you write)

1. **Real values only** — use actual column names, country names, and numeric ranges from `ds`. Never generate placeholder strings like `<col>`.
2. **Safe column access** — always use `.dropna()` before numeric operations; use `.copy()` after slicing to avoid `SettingWithCopyWarning`.
3. **Fallback for missing libraries** — wrap `linearmodels` in `if HAS_LINEARMODELS:` blocks; provide a statsmodels-based workaround for Fixed Effects using entity dummies (`pd.get_dummies`).
4. **Output directory** — always call `os.makedirs("outputs", exist_ok=True)` before saving any file (already done in Setup cell — do not repeat).
5. **McKinsey style** — every figure must call `fig.patch.set_facecolor(BG_DARK)`, `ax.set_facecolor(BG_DARK)`, and `for s in ax.spines.values(): s.set_visible(False)`.
6. **Save all charts** — every `plt.show()` must be preceded by `plt.savefig(...)`.
7. **Display tables** — use `display()` for DataFrames inside notebook cells (renders as styled HTML in Jupyter).
8. **Synthesis numbers** — the Plain-Language Synthesis cell must contain actual computed numbers, not `[X]` placeholders. Write those cells *after* mentally running through the analysis using the `ds` metadata.
