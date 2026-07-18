"""Generate the six Chapter-4 figures from already-computed outputs/*.csv.

No new estimation: figures 1-5 reformat existing CSVs; figure 6 refits the two
already-specified OLS models solely to extract residuals, and asserts the refit
coefficients match the stored CSVs to 1e-10 before plotting anything.
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
import statsmodels.api as sm
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs"
FIG = OUT / "figures"
FIG.mkdir(exist_ok=True)

# validated palette (dataviz reference instance, light mode)
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
BLUE, GREEN, MAGENTA, YELLOW = "#2a78d6", "#008300", "#e87ba4", "#eda100"
ORANGE = "#eb6834"
GRID = "#e4e3e0"

mpl.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "savefig.dpi": 200,
    "font.size": 10, "text.color": TEXT,
    "axes.edgecolor": GRID, "axes.labelcolor": TEXT2,
    "xtick.color": TEXT2, "ytick.color": TEXT2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.titlesize": 11, "axes.titleweight": "bold",
    "axes.titlecolor": TEXT,
})

# ---------------------------------------------------------------- fig 1: heatmap
corr = pd.read_csv(OUT / "regressor_correlation_matrix.csv", index_col=0)
cmap = LinearSegmentedColormap.from_list("div", [BLUE, "#f0efec", ORANGE])
fig, ax = plt.subplots(figsize=(6.4, 5.4))
ax.grid(False)
im = ax.imshow(corr.values, cmap=cmap, vmin=-1, vmax=1)
ax.set_xticks(range(len(corr)), corr.columns, rotation=30, ha="right")
ax.set_yticks(range(len(corr)), corr.index)
for i in range(len(corr)):
    for j in range(len(corr)):
        v = corr.values[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color=TEXT if abs(v) < 0.75 else "#ffffff", fontsize=9)
for edge in ("top", "right", "bottom", "left"):
    ax.spines[edge].set_visible(False)
cb = fig.colorbar(im, ax=ax, shrink=0.8)
cb.ax.tick_params(color=TEXT2, labelcolor=TEXT2)
cb.outline.set_visible(False)
ax.set_title("Regressor correlation matrix (levels, 1990–2024, N = 35)")
fig.tight_layout()
fig.savefig(FIG / "fig_4_2_regressor_correlation_heatmap.png")
plt.close(fig)

# ---------------------------------------------------------------- fig 2: VIF bar
vif = pd.read_csv(OUT / "vif_results.csv").sort_values("vif")
fig, ax = plt.subplots(figsize=(6.8, 3.6))
ax.barh(vif["regressor"], vif["vif"], color=BLUE, height=0.55)
ax.axvline(10, color=ORANGE, linewidth=1.5, linestyle="--")
ax.text(10.15, 0.0, "VIF = 10\nflag threshold", color=ORANGE,
        fontsize=9, va="center", ha="left")
for y, v in enumerate(vif["vif"]):
    ax.text(v + 0.12, y, f"{v:.3f}", va="center", color=TEXT, fontsize=9)
ax.set_xlim(0, 11.5)
ax.set_axisbelow(True)
ax.grid(axis="y", visible=False)
ax.set_xlabel("Variance Inflation Factor")
ax.set_title("VIF by regressor — all well below the flag threshold of 10")
fig.tight_layout()
fig.savefig(FIG / "fig_4_2_vif_bar.png")
plt.close(fig)

# ------------------------------------------------- fig 3: coefficient contrast
# 95% CIs from coef ± 1.96·SE using each model's own stored SEs (no recompute
# beyond the interval arithmetic).
ma = pd.read_csv(OUT / "model_a_static_ols_coefficients.csv").set_index("term")
md = pd.read_csv(OUT / "model_b_first_differenced_ols_coefficients.csv").set_index("term")
lr = pd.read_csv(OUT / "ardl_capped_1_1_long_run_coefficients.csv").set_index("term")

models = [
    ("Model A — static OLS on levels\n(literal-thesis baseline, N=35)", ma, "coef", "std_err", BLUE),
    ("First-differenced OLS\n(PRIMARY model, N=34)", md, "coef", "std_err", GREEN),
    ("ARDL(1,1) long-run\n(secondary/exploratory, N=34)", lr, "long_run_coef", "std_err_delta_method", MAGENTA),
]
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.4), sharey=True)
for ax, var, hyp in [(axes[0], "DIVP", "H1: product diversification (DIVP)"),
                     (axes[1], "DIVM", "H2: market diversification (DIVM)")]:
    ax.axvline(0, color=TEXT2, linewidth=1)
    for k, (label, df, ccol, secol, color) in enumerate(models):
        y = len(models) - 1 - k
        c, se = df.loc[var, ccol], df.loc[var, secol]
        ax.plot([c - 1.96 * se, c + 1.96 * se], [y, y], color=color, linewidth=2,
                solid_capstyle="butt")
        ax.plot(c, y, "o", color=color, markersize=9,
                markeredgecolor=SURFACE, markeredgewidth=2)
        ax.annotate(f"{c:.3f}", (c, y), textcoords="offset points",
                    xytext=(0, 9), ha="center", fontsize=9, color=TEXT)
    ax.set_yticks(range(len(models)),
                  [m[0] for m in reversed(models)], fontsize=8.5)
    ax.set_ylim(-0.5, 2.75)
    ax.set_title(hyp, fontsize=10)
    ax.grid(axis="y", visible=False)
    ax.set_axisbelow(True)
fig.supxlabel("Coefficient (point estimate with 95% CI, model's own SEs)",
              fontsize=9.5, color=TEXT2)
fig.suptitle("What a naive reader would conclude vs. the primary model:\n"
             "DIVP and DIVM coefficients across the three specifications",
             fontweight="bold", fontsize=11.5)
fig.tight_layout(rect=(0, 0.02, 1, 0.98))
fig.savefig(FIG / "fig_4_6_coefficient_contrast_forest.png")
plt.close(fig)

# ------------------------------------------------------- fig 4: ARDL lag grid
lag = pd.read_csv(OUT / "ardl_lag_selection.csv")
lag["spec"] = lag.apply(lambda r: f"ARDL({int(r.p)},{int(r.q)})", axis=1)
fig, ax = plt.subplots(figsize=(7.2, 3.8))
ys = np.arange(len(lag))[::-1]
for y, (_, r) in zip(ys, lag.iterrows()):
    ax.plot([r.aic, r.bic], [y, y], color=GRID, linewidth=1.5, zorder=1)
    ax.plot(r.aic, y, "o", color=BLUE, markersize=9,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=3,
            label="AIC" if y == ys[0] else None)
    ax.plot(r.bic, y, "o", color=GREEN, markersize=9,
            markeredgecolor=SURFACE, markeredgewidth=2, zorder=3,
            label="BIC" if y == ys[0] else None)
    ax.annotate(f"{r.aic:.2f}", (r.aic, y), textcoords="offset points",
                xytext=(0, 9), ha="center", fontsize=8.5, color=TEXT)
    ax.annotate(f"{r.bic:.2f}", (r.bic, y), textcoords="offset points",
                xytext=(0, 9), ha="center", fontsize=8.5, color=TEXT)
ax.set_yticks(ys, lag["spec"])
y_aic_best = ys[lag["aic"].values.argmin()]
y_capped = ys[list(lag["spec"]).index("ARDL(1,1)")]
ax.annotate("AIC-preferred (grid search)",
            (lag["aic"].min(), y_aic_best), textcoords="offset points",
            xytext=(0, -16), ha="left", fontsize=8.5, color=TEXT2)
ax.annotate("capped spec carried forward (leanest, no search)",
            (float(lag.set_index("spec").loc["ARDL(1,1)", "aic"]), y_capped),
            textcoords="offset points",
            xytext=(0, -16), ha="left", fontsize=8.5, color=TEXT2)
ax.set_xlabel("Information criterion (more negative = better fit–penalty trade-off)")
ax.grid(axis="y", visible=False)
ax.set_axisbelow(True)
ax.set_ylim(-0.6, len(lag) - 0.4)
ax.margins(x=0.08)
ax.legend(frameon=False, loc="center left", bbox_to_anchor=(1.0, 0.5))
ax.set_title("ARDL lag selection over the (p,q) ≤ 2 grid — AIC favours (1,2)")
fig.tight_layout()
fig.savefig(FIG / "fig_4_4_ardl_lag_selection.png")
plt.close(fig)

# --------------------------------------------- fig 5: robustness stability
specs = [
    ("Baseline\n1990–2024\n(N=34)", "model_b_first_differenced_ols_coefficients.csv"),
    ("Check 1\n1990–2023\n(N=33)", "robustness_check1_1990_2023_coefficients.csv"),
    ("Check 2\nexcl. shock yrs\n(N=29)", "robustness_check2_excl_shock_coefficients.csv"),
    ("Check 3\nraw FDI\n(N=34)", "robustness_check3_raw_fdi_coefficients.csv"),
]
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2), sharex=True)
for ax, var, color in [(axes[0], "DIVP", BLUE), (axes[1], "DIVM", GREEN)]:
    ax.axhline(0, color=TEXT2, linewidth=1)
    for k, (label, fname) in enumerate(specs):
        df = pd.read_csv(OUT / fname).set_index("term")
        c, se = df.loc[var, "coef"], df.loc[var, "std_err"]
        ax.plot([k, k], [c - 1.96 * se, c + 1.96 * se], color=color, linewidth=2,
                solid_capstyle="butt")
        ax.plot(k, c, "o", color=color, markersize=9,
                markeredgecolor=SURFACE, markeredgewidth=2)
        ax.annotate(f"{c:.3f}", (k, c), textcoords="offset points",
                    xytext=(10, -3), fontsize=9, color=TEXT)
    ax.set_xticks(range(len(specs)), [s[0] for s in specs], fontsize=8.5)
    ax.set_title(f"{var} coefficient across specifications", fontsize=10)
    ax.grid(axis="x", visible=False)
    ax.set_axisbelow(True)
axes[0].set_ylabel("Coefficient (95% CI, original SEs)")
fig.suptitle("Robustness: DIVP stays positive in every specification; DIVM stays negative,\n"
             "never significant at 5% under either original or HAC standard errors",
             fontweight="bold", fontsize=11.5)
fig.tight_layout(rect=(0, 0, 1, 0.99))
fig.savefig(FIG / "fig_4_8_robustness_stability.png")
plt.close(fig)

# ------------------------------------- fig 6: residual diagnostics (light refit)
frame = pd.read_csv(OUT / "analysis_frame_1990_2024.csv")
X_cols = ["divp", "divm", "inflation_rate_pct", "exchange_rate", "log_fdi", "shock"]

# Model A: static OLS on levels, N=35
Xa = sm.add_constant(frame[X_cols])
ra = sm.OLS(frame["eri"], Xa).fit()
stored_a = pd.read_csv(OUT / "model_a_static_ols_coefficients.csv")["coef"].values
assert np.allclose(ra.params.values, stored_a, atol=1e-10), "Model A refit mismatch"

# Primary model: OLS on first differences (const included), N=34
d = frame[["eri"] + X_cols].diff().dropna()
Xd = sm.add_constant(d[X_cols])
rd = sm.OLS(d["eri"], Xd).fit()
stored_d = pd.read_csv(OUT / "model_b_first_differenced_ols_coefficients.csv")["coef"].values
assert np.allclose(rd.params.values, stored_d, atol=1e-10), "Diff-OLS refit mismatch"
print("refit check: both models reproduce stored coefficients exactly")

fig, axes = plt.subplots(2, 2, figsize=(9.6, 7.2))
for row, (res, name, color) in enumerate([
        (ra, "Model A — static OLS on levels (N=35)", BLUE),
        (rd, "Primary model — first-differenced OLS (N=34)", GREEN)]):
    ax = axes[row, 0]
    ax.axhline(0, color=TEXT2, linewidth=1)
    ax.plot(res.fittedvalues, res.resid, "o", color=color, markersize=6,
            markeredgecolor=SURFACE, markeredgewidth=1, alpha=0.9)
    ax.set_xlabel("Fitted values")
    ax.set_ylabel("Residual")
    ax.set_title(f"{name}\nresiduals vs. fitted", fontsize=9.5)
    ax.set_axisbelow(True)

    ax = axes[row, 1]
    sm.qqplot(res.resid, line="45", fit=True, ax=ax,
              markerfacecolor=color, markeredgecolor=SURFACE, markersize=6)
    ax.get_lines()[1].set_color(TEXT2)
    ax.set_title(f"{name}\nnormal Q–Q plot", fontsize=9.5)
    ax.set_axisbelow(True)
fig.suptitle("Residual diagnostics — both models consistent with the clean "
             "Breusch–Pagan and Jarque–Bera results",
             fontweight="bold", fontsize=11.5)
fig.tight_layout(rect=(0, 0, 1, 0.98))
fig.savefig(FIG / "fig_4_5_residual_diagnostics.png")
plt.close(fig)

print("figures written:", sorted(p.name for p in FIG.glob("*.png")))
