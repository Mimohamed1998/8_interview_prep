# Plan — Final Summary (Thesis Chapter 4 Draft: Empirical Analysis and Findings)

**Parent requirement:** [research_plan.md § f "Summarize the result"](../../1_requirements/research_plan.md) plus the
"Additional requirements" (Audience and purpose, Flag deviations, Output format).
**Depends on:** all eleven completed pipeline notebooks (`pipelines/analysis/i_*.ipynb` through
`viii_*.ipynb`, plus `a_model_a_static_ols.ipynb`, `b_model_b_ardl_bounds_testing.ipynb`,
`c_shared_requirements_for_both_models.ipynb`) and every artifact under `outputs/` (49 CSVs, 3 PNGs)
that they already produced.
**Feeds into:** nothing — this is the terminal deliverable (`readme.md` workflow steps 9–11: "final
synthesis" → "validate the synthesis" → "get the graphs and put them into the main table").

## 0. What this plan is / isn't

The analysis is done: 11 notebooks have been executed, and their outputs are self-audited
(`reasoning_narrative_coverage.csv`, `significance_convention_audit.csv`, `summary_table_completeness_check.csv`,
`output_artifacts_audit.csv`). That last file already flags the Chapter 4 draft itself as
**PENDING** — "out of scope for this notebook... no chapter_4/ch4 file found under the project root."
This plan is for *writing that document*: turning already-computed, already-cross-checked numbers
into one formal academic report with embedded charts and tables. It is **not** a plan to re-run,
re-estimate, or re-derive anything — every number in the final report must trace back to an existing
file in `outputs/`, not be recalculated by hand while drafting.

## 1. Audience and tone

Two constraints from the requirements doc apply simultaneously and shape every section:

- **EViews cross-check reader (primary, practical).** The user will re-run every test manually, so
  the draft must keep showing work — test statistics, formulas, exact package/function used
  (`tooling_register.csv`), lag-selection criteria — not just a polished final table.
- **Thesis committee reader (formal, structural).** This is literally Chapter 4 of a quantitative
  thesis, so it must read in third-person formal academic register, use only the thesis's own
  variable names and notation (ERI, DIVP, DIVM, INF, EXR, log(FDI), SHOCK — never renamed or
  paraphrased), and flag every deviation from Ch. 3 methodology inline, not buried in an appendix.

## 2. Deliverable location and format (decision to confirm before writing)

Recommended default — flag for user confirmation, don't just assume:

- **Primary document:** `docs/4_report/chapter_4_empirical_analysis_and_findings.md` — new
  `4_report/` folder, continuing the existing `1_requirements/ → 2_plan/ → 3_dq/` numbering.
  Markdown as source of truth (diffable, easy to keep in sync with `outputs/*.csv` if a notebook is
  re-run later).
- **New charts:** saved to `outputs/figures/` (new subfolder — keeps the flat `outputs/` convention
  for data/tables intact per `output_artifacts_audit.csv`'s "no per-model subfolders" pass, while
  giving figures their own namespace) and embedded in the markdown by relative path.
- **Word export:** research_plan.md says "markdown **or** Word document" — treat `.docx` as an
  optional final step (`pandoc chapter_4_....md -o chapter_4_....docx`), not a required deliverable,
  unless the user confirms they need it.

## 3. Source map — research_plan.md § f item → notebook(s) → output files

| # | Requirement | Source notebook(s) | Key output files |
|---|---|---|---|
| 1 | Descriptive stats table + trend charts (RQ1) | `ii_descriptive_statistics_and_trend_analysis.ipynb` | `descriptive_statistics.csv`, `correlation_eri_divp_divm.csv`, `trend_eri_pdi_mdi_combined.png`, `trend_pdi.png`, `trend_mdi.png` |
| 2 | Diagnostic test results table (ADF, VIF, DW/BG/BP/JB/RESET, bounds test) | `iii_stationarity_testing.ipynb`, `iv_multicollinearity_check.ipynb`, `vii_post_estimation_diagnostics.ipynb` | `adf_stationarity_results.csv`, `vif_results.csv`, `regressor_correlation_matrix.csv`, `diagnostics_model_a_ols.csv`, `diagnostics_model_diff_ols.csv`, `diagnostics_model_b_ardl_capped.csv`, `ardl_capped_1_1_bounds_test.csv`, `ardl_bounds_test.csv`, `cusum_cusumsq_model_b_status.csv`, `hac_remediation_status.csv` |
| 3 | Model A (static OLS) regression table | `a_model_a_static_ols.ipynb` | `model_a_static_ols_coefficients.csv`, `model_a_static_ols_fit_stats.csv`, `model_a_hac_coefficients.csv` |
| 4 | Model B (ARDL) results: lag selection, bounds test, long-run/ECM/short-run tables | `b_model_b_ardl_bounds_testing.ipynb` | `ardl_lag_selection.csv`, `ardl_capped_1_1_bounds_test.csv`, `ardl_capped_1_1_long_run_coefficients.csv`, `ardl_capped_1_1_error_correction_term.csv`, `ardl_capped_1_1_short_run_coefficients.csv`, plus **primary** model `model_b_first_differenced_ols_coefficients.csv` / `..._fit_stats.csv` |
| 5 | Interpretation tied to H1/H2 | `c_shared_requirements_for_both_models.ipynb` | `h1_h2_final_verdict.csv`, `model_a_vs_b_vs_primary_contrast.csv`, `model_comparison_side_by_side.csv` |
| 6 | Discussion vs. Ch. 2 literature | *(no output file — original writing)* | `modeling_path_decision.csv` memo for the 2022-crisis/error-correction angle; **gap** — see § 9 |
| 7 | Robustness check summary | `viii_robustness_checks.ipynb` | `robustness_checks_comparison.csv`, `robustness_check1/2/3_*_coefficients.csv`, `..._fit_stats.csv`, `..._hac_coefficients.csv` |
| — | Deviation register (cross-cutting) | all notebooks | `deviations_register.csv`, `modeling_path_decision.csv` |

## 4. Table inventory

Roughly 15 report tables, each a direct reformat of a CSV — no recomputation:

- **4.1** Descriptive statistics (`descriptive_statistics.csv`: N, mean, SD, min, max, median,
  skewness, excess kurtosis, all 7 variables) + regressor correlation matrix
  (`regressor_correlation_matrix.csv`, `correlation_eri_divp_divm.csv`).
- **4.2** ADF results, levels and first differences, all 6 variables, with I(0)/I(1) conclusion
  column (`adf_stationarity_results.csv`); VIF table (`vif_results.csv`, all currently < 10 — no
  flags); the diagnostics-in-sequence table per model
  (`diagnostics_model_a_ols.csv` / `..._diff_ols.csv` / `..._model_b_ardl_capped.csv`).
- **4.3** Model A coefficients with stars, original + HAC SEs side by side
  (`model_a_static_ols_coefficients.csv` + `model_a_hac_coefficients.csv`), fit stats
  (`model_a_static_ols_fit_stats.csv`).
- **4.4** ARDL lag-selection AIC/BIC grid (`ardl_lag_selection.csv`); bounds-test table against
  Pesaran et al. (2001) critical values (`ardl_capped_1_1_bounds_test.csv`); long-run coefficients
  (`ardl_capped_1_1_long_run_coefficients.csv`); error-correction term
  (`ardl_capped_1_1_error_correction_term.csv`); short-run coefficients
  (`ardl_capped_1_1_short_run_coefficients.csv`); **primary** first-differenced OLS coefficients +
  fit stats.
- **4.6** Consolidated H1/H2 verdict table (`h1_h2_final_verdict.csv`) and the three-way
  naive-vs-secondary-vs-primary contrast (`model_a_vs_b_vs_primary_contrast.csv`,
  `model_comparison_side_by_side.csv`).
- **4.8** Robustness comparison table, baseline vs. Checks 1–3
  (`robustness_checks_comparison.csv`), each with original + HAC-robust coefficient panels.
- **4.9** Deviations register as a formatted table (`deviations_register.csv`: 5 rows).

**Formatting rules carried into every table:**
- 3 decimal places for coefficients/statistics, `***`/`**`/`*` at 1%/5%/10% (already verified
  consistent in `significance_convention_audit.csv` — reuse the stored stars, don't recompute).
- **Report N per model, never assume they match** — Model A: N=35; first-differenced OLS and
  ARDL(1,1): N=34 (one observation lost to differencing), per `summary_table_completeness_check.csv`.
  State this explicitly under any side-by-side table, since it's easy for a reader to misread the
  comparison as apples-to-apples.

## 5. Figure inventory

**Existing, reusable as-is (3):** `trend_eri_pdi_mdi_combined.png`, `trend_pdi.png`, `trend_mdi.png`
— cover requirement 1 (RQ1 trend charts with shock periods shaded).

**Missing — need to be created** (invoke the `dataviz`/`chart` skill when actually building these;
each reuses already-computed data or already-fit model objects, so none of this is new analysis):

| Figure | Purpose | Source data |
|---|---|---|
| Regressor correlation heatmap | Visual companion to the VIF table (§4.2) | `regressor_correlation_matrix.csv` |
| VIF bar chart | Show all regressors comfortably under the VIF=10 flag line | `vif_results.csv` |
| Coefficient contrast chart (forest-plot style): Model A vs. first-diff OLS vs. ARDL(1,1) long-run, DIVP and DIVM only | **The single most important figure** — visualizes exactly the "what would a naive reader conclude vs. what the primary model shows" contrast the requirements emphasize | `model_comparison_side_by_side.csv`, `h1_h2_final_verdict.csv` |
| ARDL AIC/BIC lag-grid chart (or a clearly-labeled Vsmall table if only 4 candidate lags) | Support the lag-selection narrative | `ardl_lag_selection.csv` |
| Robustness coefficient stability chart: DIVP/DIVM point estimates across baseline + Checks 1–3 | Directly supports §4.8 ("how much do the coefficients move") | `robustness_checks_comparison.csv` |
| Residual diagnostics (fitted-vs-residual, histogram/QQ) for Model A and the primary differenced OLS | Standard diagnostic visuals to accompany the DW/BP/JB/RESET table | **Gap — no per-observation residual series is saved in `outputs/`, only summary test statistics.** Producing this requires refitting the already-specified models to pull `.resid` (trivial reuse, not new estimation) — flag this as a small implementation step, not a data gap. |

**Explicitly do not fabricate:** CUSUM/CUSUMSQ stability charts for Model B. Per
`cusum_cusumsq_model_b_status.csv`, both are infeasible (rank-deficient X′X at the standard skip
because SHOCK=0 for the first 18 of 34 observations) and were deliberately skipped, not omitted by
oversight. Report this as a one-paragraph note with the reason, not a chart.

## 6. Report outline

1. **4.0** Brief chapter roadmap paragraph (what RQ1/RQ2 and H1/H2 are, and the order the chapter
   answers them in).
2. **4.1 Descriptive Statistics and Trends (RQ1)** — table + 3 trend charts + plain-language read
   (is MDI consistently above PDI? structural break near 2022?).
3. **4.2 Diagnostic Testing Sequence** — ADF (levels + differences) → VIF/correlation → decision
   branch outcome (Branch B: mixed I(0)/I(1), no I(2)) → what that implies for the modeling choice.
4. **4.3 Model A — Static OLS (Literal-Thesis Baseline)** — spec, table, fit stats. Flag the
   log(FDI) deviation here, at first use, not only in §4.9.
5. **4.4 Model B — ARDL Bounds Testing and the First-Differenced OLS Primary Model** — lag
   selection, bounds test (inconclusive at both specs), long-run/ECM/short-run tables, **then a
   clearly separated subsection narrating the 2026-07-17 primary-model redesignation** (why ARDL
   was demoted to secondary/exploratory: bounds test never confirmed cointegration + Breusch-Godfrey
   lag-2 flagged serial correlation) with the differenced OLS presented as primary.
6. **4.5 Post-Estimation Diagnostics** — organized per model (A / primary differenced OLS / ARDL),
   DW-or-BG as applicable, BP, JB, RESET, HAC remediation note, CUSUM/CUSUMSQ infeasibility note.
7. **4.6 Hypothesis Testing: H1 and H2** — verdict table, both statistical and economic significance
   (e.g., "a 0.1 increase in DIVP is associated with a Δ ERI of X"), using the primary model's
   coefficients as the evidentiary basis per `h1_h2_final_verdict.csv`.
8. **4.7 Discussion** — tie to Ch. 2 literature (product vs. market diversification debate), and the
   2022 crisis's appearance in SHOCK/residuals/error-correction speed. **Depends on the thesis PDF
   for citation-consistent framing — see § 9 gap.**
9. **4.8 Robustness Checks** — 1990–2023 subset, shock-year exclusion, raw FDI, alternate ARDL lag;
   how much DIVP/DIVM move; stability chart.
10. **4.9 Summary of Deviations from Literal Thesis Methodology** — consolidated table from
    `deviations_register.csv` (5 deviations), each cross-referenced back to the section where it was
    first flagged inline.
11. **4.10 Chapter Summary** — one paragraph bridging to a discussion/conclusion chapter.

## 7. Deviation handling

Flag deviations **twice**, per the requirements doc's "call it out explicitly... rather than
silently making the change": inline at first occurrence (log-FDI in §4.3; ARDL triggered in §4.2/4.4;
1990–2024 extension in §4.1; JB/RESET additions in §4.5; primary-model redesignation as its own
labeled subsection in §4.4) **and** as the consolidated table in §4.9. Don't rely on §4.9 alone —
a reader working through the chapter sequentially should hit each flag exactly where it changes
what they're reading.

## 8. Writing process (for the implementation step that follows this plan)

1. Spot-check a handful of CSVs against their source notebook's last-executed cell output, to
   confirm nothing changed since these files were written (light consistency check — not a
   pipeline re-run).
2. Draft section-by-section in the § 6 order, pulling every number directly from its source CSV.
3. Generate the six missing figures (§ 5) by reusing already-fit model objects / already-computed
   tables — no new estimation — and save to `outputs/figures/`.
4. Assemble the ~15 tables (§ 4) with consistent formatting; footnote N differences explicitly.
5. Insert deviation flags inline (§ 7) plus the consolidated §4.9 table.
6. Write § 4.7 Discussion — if the thesis PDF isn't available in that session, stub it with a
   clearly marked placeholder rather than inventing literature framing.
7. Self-audit pass: check every number in the draft against its source CSV, mirroring the audit
   discipline already used in `c_shared_requirements_for_both_models.ipynb`.
8. Optional: `pandoc` markdown → `.docx` export, only if confirmed needed (§ 2).

## 9. Open decisions to confirm before writing (flag, don't guess)

- **Deliverable path/format** — confirm `docs/4_report/chapter_4_empirical_analysis_and_findings.md`
  + `outputs/figures/`, or a different location.
- **Thesis PDF availability** — § 4.7's literature discussion needs Ch. 1–2 of the thesis PDF for
  citation-consistent framing and terminology; it was not attached to this session. Confirm whether
  it will be supplied for the write-up step, or whether that section should be stubbed.
- **Residual diagnostic plots** — confirm it's fine to lightly refit Model A and the primary
  differenced-OLS model solely to extract `.resid` for the two diagnostic plots (§ 5), since no
  residual series is currently saved to `outputs/`.
- **Word export** — confirm whether a `.docx` is actually required, or markdown alone satisfies the
  deliverable.

## Definition of done (for this planning step)

- Every item in research_plan.md § f (1–7) mapped to its exact source notebook(s) and output
  file(s) — no ambiguity about where a number in the eventual report comes from.
- Complete table inventory (§ 4) and figure inventory (§ 5), with gaps (residual series,
  6 missing charts) explicitly identified rather than assumed away.
- Deviation-handling approach specified (inline + consolidated, not consolidated-only).
- Open decisions (§ 9) flagged for user confirmation before the report itself is drafted.
