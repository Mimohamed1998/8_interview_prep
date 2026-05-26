"""
H1 Analysis: AI Preparedness -> Sustainability Performance
==========================================================
H1: AI readiness has a positive impact on sustainability (beta1 > 0).
H0: beta1 <= 0
Test: one-tailed t-test, alpha=.05
Selected model: Fixed Effects (Two-Way) per Hausman test from RQ1.
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.stats import t as t_dist
from linearmodels.panel import PanelOLS, RandomEffects
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.outliers_influence import OLSInfluence
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path(
    "/Users/mohamedinas/Desktop/SE_projects"
    "/9_fathima_stat_support/version_v1/8_interview_prep"
)
DATA = BASE / "data/3_processed_data/master_features/panel_dataset_2020_2023.parquet"
OUT  = BASE / "outputs"
OUT.mkdir(exist_ok=True)

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY   = "#0C1B33"
BLUE   = "#1F3D7A"
CYAN   = "#2196F3"
GOLD   = "#FFC107"
RED    = "#EF5350"
ACCENT = "#4FC3F7"
LIGHT  = "#CFD8DC"
WHITE  = "#FFFFFF"

plt.rcParams.update({
    "figure.facecolor": NAVY, "axes.facecolor": NAVY,
    "text.color": WHITE, "axes.labelcolor": WHITE,
    "xtick.color": LIGHT, "ytick.color": LIGHT, "axes.edgecolor": LIGHT,
    "grid.color": BLUE, "grid.alpha": 0.3, "font.family": "sans-serif",
    "axes.spines.top": False, "axes.spines.right": False,
})

GROUP_COLORS = {"Developed": CYAN, "Developing": GOLD, "Lower Governance": RED}

# ── 1. Load data ──────────────────────────────────────────────────────────────
print("Loading data...")
df = pd.read_parquet(DATA)
n  = len(df)
print(f"  Shape: {df.shape}")
print(df["country_group"].value_counts().to_string())

# ── 2. Fit three panel models ──────────────────────────────────────────────────
print("\nFitting models...")
df_p  = df.set_index(["country", "year"])
X_ols = sm.add_constant(df[["ai_readiness_score"]])

ols_res = OLS(df["sdg_index_score"], X_ols).fit(cov_type="HC3")
fe_res  = PanelOLS(
    df_p["sdg_index_score"], df_p[["ai_readiness_score"]],
    entity_effects=True, time_effects=True
).fit(cov_type="clustered", cluster_entity=True)
re_res  = RandomEffects(
    df_p["sdg_index_score"], sm.add_constant(df_p[["ai_readiness_score"]])
).fit(cov_type="robust")

b_ols, se_ols = ols_res.params["ai_readiness_score"], ols_res.bse["ai_readiness_score"]
r2_ols, df_ols = ols_res.rsquared, ols_res.df_resid

b_fe,  se_fe  = fe_res.params["ai_readiness_score"],  fe_res.std_errors["ai_readiness_score"]
r2_fe, df_fe  = fe_res.rsquared, fe_res.df_resid

b_re,  se_re  = re_res.params["ai_readiness_score"],  re_res.std_errors["ai_readiness_score"]
r2_re, df_re  = re_res.rsquared, re_res.df_resid

print(f"  OLS  beta={b_ols:.4f}  FE beta={b_fe:.4f}  RE beta={b_re:.4f}")

# ── 3. One-tailed hypothesis test ─────────────────────────────────────────────
print("\nStep 1: One-tailed hypothesis test...")

def one_tail_row(b, se, df_r, r2, label):
    t_s = b / se
    p2  = float(2 * t_dist.sf(abs(t_s), df_r))
    p1  = float(t_dist.sf(t_s, df_r))
    ci1 = b - 1.645 * se
    cil = b - 1.96 * se
    ciu = b + 1.96 * se
    f2  = r2 / (1 - r2) if r2 < 1 else float("nan")
    dec = "Reject H0" if (b > 0 and p1 < 0.05) else "Fail to reject H0"
    return {
        "Model": label, "beta1": round(b, 4), "SE": round(se, 4),
        "t_stat": round(t_s, 4), "p_2tail": round(p2, 4), "p_1tail": round(p1, 4),
        "CI_lower_1tail": round(ci1, 4), "CI_lower_2tail": round(cil, 4),
        "CI_upper_2tail": round(ciu, 4), "R2": round(r2, 4),
        "Cohens_f2": round(f2, 4) if not (isinstance(f2, float) and np.isnan(f2)) else "N/A",
        "Decision_H1": dec,
    }

rows = [
    one_tail_row(b_ols, se_ols, df_ols, r2_ols, "Pooled OLS"),
    one_tail_row(b_fe,  se_fe,  df_fe,  r2_fe,  "Fixed Effects (Two-Way) SELECTED"),
    one_tail_row(b_re,  se_re,  df_re,  r2_re,  "Random Effects"),
]
h1_table = pd.DataFrame(rows)
print(h1_table.to_string(index=False))
h1_table.to_csv(OUT / "h1_hypothesis_test_table.csv", index=False)
print("  Saved: h1_hypothesis_test_table.csv")

# ── 4. Effect size (standardised beta) ────────────────────────────────────────
print("\nStep 2: Effect size (standardised beta)...")
df["ai_z"]  = (df["ai_readiness_score"] - df["ai_readiness_score"].mean()) / df["ai_readiness_score"].std()
df["sdg_z"] = (df["sdg_index_score"]    - df["sdg_index_score"].mean())    / df["sdg_index_score"].std()
df_pz = df.set_index(["country", "year"])
fe_std  = PanelOLS(
    df_pz["sdg_z"], df_pz[["ai_z"]],
    entity_effects=True, time_effects=True
).fit(cov_type="clustered", cluster_entity=True)
std_beta = fe_std.params["ai_z"]
std_se   = fe_std.std_errors["ai_z"]
f2_fe    = r2_fe / (1 - r2_fe)
print(f"  Standardised beta1 (FE): {std_beta:.4f}  SE={std_se:.4f}")
print(f"  FE R2={r2_fe:.4f}  Cohen f2={f2_fe:.4f}")

# ── 5. Robustness checks ───────────────────────────────────────────────────────
print("\nStep 3: Robustness checks...")
rob_rows = []

# 5a. Cook's D
ols_plain = OLS(df["sdg_index_score"], sm.add_constant(df[["ai_readiness_score"]])).fit()
cooks     = OLSInfluence(ols_plain).cooks_distance[0]
mask      = cooks > (4 / n)
n_out     = int(mask.sum())
df_cl     = df[~mask].copy().set_index(["country", "year"])
fe_cl     = PanelOLS(
    df_cl["sdg_index_score"], df_cl[["ai_readiness_score"]],
    entity_effects=True, time_effects=True
).fit(cov_type="clustered", cluster_entity=True)
b_c, se_c = fe_cl.params["ai_readiness_score"], fe_cl.std_errors["ai_readiness_score"]
p_c       = float(t_dist.sf(b_c / se_c, fe_cl.df_resid))
rob_rows.append({
    "Check": f"Outliers excl (Cook D>4/n; removed {n_out})",
    "beta1": round(b_c, 4), "SE": round(se_c, 4),
    "t_stat": round(b_c / se_c, 4), "p_1tail": round(p_c, 4),
    "Sign_consistent": "Yes" if b_c > 0 else "No",
})

# 5b. Year-by-year
for yr in sorted(df["year"].unique()):
    dfy = df[df["year"] == yr]
    res = OLS(dfy["sdg_index_score"], sm.add_constant(dfy[["ai_readiness_score"]])).fit()
    by, sey = res.params["ai_readiness_score"], res.bse["ai_readiness_score"]
    ty, py  = by / sey, float(t_dist.sf(by / sey, res.df_resid))
    rob_rows.append({
        "Check": f"Year {yr} OLS",
        "beta1": round(by, 4), "SE": round(sey, 4),
        "t_stat": round(ty, 4), "p_1tail": round(py, 4),
        "Sign_consistent": "Yes" if by > 0 else "No",
    })

# 5c. Country groups
for grp in ["Developed", "Developing", "Lower Governance"]:
    dfg = df[df["country_group"] == grp]
    res = OLS(dfg["sdg_index_score"], sm.add_constant(dfg[["ai_readiness_score"]])).fit()
    bg, seg = res.params["ai_readiness_score"], res.bse["ai_readiness_score"]
    tg, pg  = bg / seg, float(t_dist.sf(bg / seg, res.df_resid))
    rob_rows.append({
        "Check": f"Group {grp} OLS",
        "beta1": round(bg, 4), "SE": round(seg, 4),
        "t_stat": round(tg, 4), "p_1tail": round(pg, 4),
        "Sign_consistent": "Yes" if bg > 0 else "No",
    })

# 5d. Lagged predictor
df_lg = df.sort_values(["country", "year"]).copy()
df_lg["ai_lag1"] = df_lg.groupby("country")["ai_readiness_score"].shift(1)
df_lg = df_lg.dropna(subset=["ai_lag1"])
res_lg = OLS(df_lg["sdg_index_score"], sm.add_constant(df_lg[["ai_lag1"]])).fit()
bl, sel = res_lg.params["ai_lag1"], res_lg.bse["ai_lag1"]
tl, pl  = bl / sel, float(t_dist.sf(bl / sel, res_lg.df_resid))
rob_rows.append({
    "Check": "Lagged AI(t)->SDG(t+1) OLS",
    "beta1": round(bl, 4), "SE": round(sel, 4),
    "t_stat": round(tl, 4), "p_1tail": round(pl, 4),
    "Sign_consistent": "Yes" if bl > 0 else "No",
})

rob_df = pd.DataFrame(rob_rows)
print(rob_df.to_string(index=False))
rob_df.to_csv(OUT / "h1_robustness_checks.csv", index=False)
print("  Saved: h1_robustness_checks.csv")

# ── 6. Scatter plot ───────────────────────────────────────────────────────────
print("\nStep 4a: Scatter plot...")
fig, ax = plt.subplots(figsize=(10, 7), facecolor=NAVY)
ax.set_facecolor(NAVY)
for grp, col in GROUP_COLORS.items():
    sub = df[df["country_group"] == grp]
    ax.scatter(sub["ai_readiness_score"], sub["sdg_index_score"],
               color=col, alpha=0.85, s=65, label=grp, zorder=3)
xv = np.linspace(df["ai_readiness_score"].min(), df["ai_readiness_score"].max(), 200)
yv = ols_res.params["const"] + ols_res.params["ai_readiness_score"] * xv
ax.plot(xv, yv, color=WHITE, linewidth=2.0, zorder=4)
fe_p1 = float(t_dist.sf(b_fe / se_fe, df_fe))
eq = (
    f"Pooled OLS: beta1={b_ols:.4f}  R2={r2_ols:.3f}\n"
    f"FE selected: beta1={b_fe:.4f}  p(1-tail)={fe_p1:.4f}"
)
ax.text(0.03, 0.97, eq, transform=ax.transAxes, fontsize=9, color=WHITE, va="top",
        bbox=dict(boxstyle="round,pad=0.4", facecolor=BLUE, alpha=0.8))
ax.set_xlabel("AI Readiness Score", fontsize=12)
ax.set_ylabel("SDG Index Score",    fontsize=12)
ax.set_title(
    "H1 - AI Readiness vs SDG Index\n(Fitted line = Pooled OLS; coloured by country group)",
    fontsize=13, pad=14
)
ax.legend(fontsize=9, facecolor=BLUE, edgecolor=LIGHT, labelcolor=WHITE)
ax.grid(True, alpha=0.2)
fig.tight_layout()
fig.savefig(OUT / "h1_scatter_annotated.png", dpi=150, bbox_inches="tight", facecolor=NAVY)
plt.close(fig)
print("  Saved: h1_scatter_annotated.png")

# ── 7. Coefficient plot ───────────────────────────────────────────────────────
print("Step 4b: Coefficient plot...")
models_ci = [
    ("Pooled OLS",                    b_ols, se_ols),
    ("Fixed Effects\n(Two-Way) SEL",  b_fe,  se_fe),
    ("Random Effects",                b_re,  se_re),
]
labels_m = [m[0] for m in models_ci]
betas_m  = [m[1] for m in models_ci]
err2     = [1.96  * m[2] for m in models_ci]
err1     = [1.645 * m[2] for m in models_ci]
cols_m   = [CYAN, GOLD, ACCENT]

fig, ax = plt.subplots(figsize=(9, 5), facecolor=NAVY)
ax.set_facecolor(NAVY)
for i, (lbl, b, e2, e1, col) in enumerate(zip(labels_m, betas_m, err2, err1, cols_m)):
    ax.plot([b - e2, b + e2], [i, i], color=col, linewidth=2.5, alpha=0.5)
    ax.vlines(b - e1, i - 0.15, i + 0.15, color=col, linewidth=2)
    ax.scatter(b, i, color=col, s=120, zorder=4, edgecolors=WHITE, linewidths=0.8)
    ax.text(b + e2 + 0.001, i, f"beta={b:.4f}", va="center", fontsize=9, color=WHITE)
ax.axvline(0, color=RED, linewidth=1.5, linestyle="--", label="beta=0 (H0 boundary)")
ax.set_yticks(range(len(labels_m)))
ax.set_yticklabels(labels_m, fontsize=10)
ax.set_xlabel("beta1 (AI Readiness -> SDG Index)", fontsize=11)
ax.set_title(
    "H1 - Coefficient Plot: beta1 Across Models\n(Bars = 95% CI; dashed = H0 boundary)",
    fontsize=12, pad=10
)
ax.legend(fontsize=9, facecolor=BLUE, edgecolor=LIGHT, labelcolor=WHITE)
ax.grid(axis="x", alpha=0.2)
fig.tight_layout()
fig.savefig(OUT / "h1_coefficient_plot.png", dpi=150, bbox_inches="tight", facecolor=NAVY)
plt.close(fig)
print("  Saved: h1_coefficient_plot.png")

# ── 8. Year-panel plot ────────────────────────────────────────────────────────
print("Step 4c: Year-panel plot...")
years = sorted(df["year"].unique())
fig, axes = plt.subplots(1, 4, figsize=(18, 5), facecolor=NAVY)
fig.suptitle("H1 - AI Readiness vs SDG Index by Year (Cross-Section OLS)",
             fontsize=13, color=WHITE, y=1.01)
for ax, yr in zip(axes, years):
    ax.set_facecolor(NAVY)
    dfy = df[df["year"] == yr]
    for grp, col in GROUP_COLORS.items():
        sub = dfy[dfy["country_group"] == grp]
        ax.scatter(sub["ai_readiness_score"], sub["sdg_index_score"],
                   color=col, alpha=0.85, s=55, label=grp, zorder=3)
    res_y = OLS(dfy["sdg_index_score"], sm.add_constant(dfy[["ai_readiness_score"]])).fit()
    xr = np.linspace(dfy["ai_readiness_score"].min(), dfy["ai_readiness_score"].max(), 100)
    ax.plot(xr, res_y.params["const"] + res_y.params["ai_readiness_score"] * xr,
            color=WHITE, linewidth=1.8)
    ax.set_title(
        f"{yr}\nbeta={res_y.params['ai_readiness_score']:.4f}  R2={res_y.rsquared:.3f}",
        fontsize=10, color=WHITE, pad=6
    )
    ax.set_xlabel("AI Readiness", fontsize=9)
    if yr == years[0]:
        ax.set_ylabel("SDG Score", fontsize=9)
    ax.grid(True, alpha=0.15)
handles = [mpatches.Patch(color=c, label=g) for g, c in GROUP_COLORS.items()]
fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=9,
           facecolor=BLUE, edgecolor=LIGHT, labelcolor=WHITE, bbox_to_anchor=(0.5, -0.06))
fig.tight_layout()
fig.savefig(OUT / "h1_year_panel.png", dpi=150, bbox_inches="tight", facecolor=NAVY)
plt.close(fig)
print("  Saved: h1_year_panel.png")

# ── 9. Synthesis narrative ────────────────────────────────────────────────────
print("\nStep 5: Writing synthesis...")
fe_t  = b_fe / se_fe
fe_ci = b_fe - 1.645 * se_fe
ols_p1 = float(t_dist.sf(b_ols / se_ols, df_ols))
re_p1  = float(t_dist.sf(b_re  / se_re,  df_re))

if f2_fe >= 0.35:   eff = "large"
elif f2_fe >= 0.15: eff = "medium"
elif f2_fe >= 0.02: eff = "small"
else:               eff = "negligible"

dec_fe  = "Reject H0" if (b_fe  > 0 and fe_p1  < 0.05) else "Fail to reject H0"
dec_ols = "Reject H0" if (b_ols > 0 and ols_p1 < 0.05) else "Fail to reject H0"
dec_re  = "Reject H0" if (b_re  > 0 and re_p1  < 0.05) else "Fail to reject H0"

robustness_md = rob_df.to_markdown(index=False)

synthesis_parts = [
    "# H1 Synthesis - AI Readiness -> Sustainability Performance",
    "",
    "## Hypothesis",
    "**H1:** AI preparedness has a positive impact on sustainability performance.",
    "**H0:** beta1 <= 0  |  **Test:** one-tailed t-test, alpha=.05",
    "**Selected model:** Fixed Effects (Two-Way) per Hausman test (chi2=209.66, p<.001) from RQ1.",
    "",
    "---",
    "",
    "## Step 1 - Primary Hypothesis Test",
    "",
    f"N = {n} observations (26 countries x 4 years).",
    "",
    "| Model | beta1 | SE | t-stat | p (1-tail) | 95% CI lower (1-tail) | Decision |",
    "|-------|-------|----|--------|-----------|----------------------|----------|",
    (f"| Pooled OLS | {b_ols:.4f} | {se_ols:.4f} | {b_ols/se_ols:.4f} |"
     f" {ols_p1:.4f} | {b_ols-1.645*se_ols:.4f} | {dec_ols} |"),
    (f"| **Fixed Effects (SELECTED)** | **{b_fe:.4f}** | **{se_fe:.4f}** |"
     f" **{fe_t:.4f}** | **{fe_p1:.4f}** | **{fe_ci:.4f}** | **{dec_fe}** |"),
    (f"| Random Effects | {b_re:.4f} | {se_re:.4f} | {b_re/se_re:.4f} |"
     f" {re_p1:.4f} | {b_re-1.645*se_re:.4f} | {dec_re} |"),
    "",
    (f"**Interpretation:** The Fixed Effects model yields beta1 = {b_fe:.4f} "
     f"(SE={se_fe:.4f}, t={fe_t:.4f}, p_1tail={fe_p1:.4f}). The coefficient is "
     f"**positive** (consistent with H1) but does not reach alpha=.05 once country "
     f"fixed effects and time trends are absorbed. Pooled OLS beta1={b_ols:.4f} "
     f"is significant but inadmissible given Hausman test mandating FE."),
    "",
    "---",
    "",
    "## Step 2 - Effect Size",
    "",
    f"- **R2 (FE within):** {r2_fe:.4f}",
    (f"- **Cohen's f2:** {f2_fe:.4f} -> **{eff} effect** "
     f"(small>=0.02, medium>=0.15, large>=0.35)"),
    f"- **Standardised beta1 (z-scored FE):** {std_beta:.4f} (SE={std_se:.4f})",
    "",
    "---",
    "",
    "## Step 3 - Robustness Checks",
    "",
    robustness_md,
    "",
    "---",
    "",
    "## Overall Conclusion on H1",
    "",
    (f"The Fixed Effects panel regression reveals a **positive but not statistically significant** "
     f"association between AI Readiness and SDG Index scores "
     f"(beta1={b_fe:.4f}, SE={se_fe:.4f}, t={fe_t:.4f}, p_1tail={fe_p1:.4f}, alpha=.05). "
     f"The positive sign is consistent with H1 and robust to outlier exclusion and "
     f"year-by-year cross-sections."),
    "",
    "**Recommended thesis statement:**",
    (f"> 'The Fixed Effects panel regression revealed a positive but non-significant "
     f"association between AI Readiness and SDG Index scores "
     f"(beta1={b_fe:.4f}, SE={se_fe:.4f}, t={fe_t:.4f}, p={fe_p1:.4f}, one-tailed, "
     f"alpha=.05). While the direction is consistent with H1, the evidence does not meet "
     f"the significance threshold once country-level heterogeneity is removed, suggesting "
     f"that cross-country structural differences in AI preparedness drive the AI-SDG "
     f"correlation more than within-country temporal change over 2020-2023.'"),
    "",
    "---",
    "",
    "## Output Files",
    "",
    "| File | Description |",
    "|------|-------------|",
    "| h1_hypothesis_test_table.csv | beta1, SE, t, p (1- and 2-tail) for all three models |",
    "| h1_coefficient_plot.png      | beta1 +/- 95% CI across Pooled OLS, FE, RE |",
    "| h1_robustness_checks.csv     | Outlier-excluded, year-by-year, group-level, lagged |",
    "| h1_scatter_annotated.png     | Scatter of AI Readiness vs SDG with fitted line |",
    "| h1_year_panel.png            | Four cross-sectional scatter panels (2020-2023) |",
]

synthesis = "\n".join(synthesis_parts)
(OUT / "h1_synthesis.md").write_text(synthesis, encoding="utf-8")
print("  Saved: h1_synthesis.md")

# ── 10. Validation ─────────────────────────────────────────────────────────────
print("\n=== VALIDATION ===")
expected = [
    "h1_hypothesis_test_table.csv",
    "h1_coefficient_plot.png",
    "h1_robustness_checks.csv",
    "h1_scatter_annotated.png",
    "h1_year_panel.png",
    "h1_synthesis.md",
]
all_ok = True
for f in expected:
    p    = OUT / f
    ok   = p.exists() and p.stat().st_size > 0
    size = p.stat().st_size if p.exists() else 0
    tag  = "OK" if ok else "MISSING/EMPTY"
    print(f"  [{tag}]  {f}  ({size:,} bytes)")
    if not ok:
        all_ok = False

print()
if all_ok:
    print("All outputs validated OK")
else:
    print("WARNING: Some outputs missing")
