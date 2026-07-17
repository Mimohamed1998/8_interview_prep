# Plan e.C — Shared Requirements for Both Models

**Parent requirement:** [research_plan.md § e — "For both models"](../../1_requirements/research_plan.md)
**Depends on:** [a — Model A: Static OLS](a_model_a_static_ols.md); [b — Model B: ARDL bounds
testing](b_model_b_ardl_bounds_testing.md) (governs conventions for whichever of these is
estimated)
**Feeds into:** [analysis/vi — Estimation](../analysis/vi_estimation.md); [analysis/vii —
Post-estimation diagnostics](../analysis/vii_post_estimation_diagnostics.md); Chapter 4 draft
(all sections referencing model output)

## Objective

Capture the conventions, reporting standards, and narrative obligations that apply to **whichever
model(s) are estimated** — Model A always, Model B conditionally — so they are stated once here
rather than repeated (and risking drift) across both model-specific plans. This document is
reporting/process convention, not a model specification; [a](a_model_a_static_ols.md) and
[b](b_model_b_ardl_bounds_testing.md) own the actual equations and estimation steps.

## Requirements

### 1. Estimation tooling — stated explicitly per model

- **Model A:** `statsmodels.api.OLS`.
- **Model B:** `statsmodels.tsa.ardl.ARDL` (or an equivalent bounds-testing implementation).
- State the exact package/function/API call used for each model wherever its output is
  presented — not just once at the top of the document — since the user cross-checks every
  number against EViews' `LS` command (Model A) and ARDL wizard (Model B), and the specific
  implementation choice (e.g. how an intercept/trend case is handled) is the most common source
  of a Python-vs-EViews mismatch.

### 2. Summary table completeness

Every regression table produced (Model A; Model B's short-run, long-run, and bounds-test
tables; the first-differenced OLS comparison) must report, at minimum:
- Coefficient, standard error, t-statistic, p-value — per regressor.
- R², adjusted R², F-statistic and its p-value (Model A and the first-differenced OLS; for
  Model B, the equivalent ECM-level fit statistics plus the bounds-test F-statistic).
- N (sample size actually used, which may differ from 35 once lags consume initial
  observations — state the effective N explicitly for Model B, since it will not match Model
  A's N=35 and this is a likely point of confusion against EViews output).

### 3. Significance convention

Report significance at all three conventional thresholds — 1%, 5%, 10% — using `***`/`**`/`*`
stars, consistently across every table in both models. Do not selectively report only one
threshold in one table and a different set in another.

### 4. Explain reasoning, not just output

For every test or estimation step, state *why* it comes next and what the result implies for
the next decision — not only the code and the output table. The user is cross-verifying every
number in EViews and needs to be able to follow and reproduce each step manually. This applies
throughout [analysis/](../analysis/) and both model documents, but is called out here as a
standing requirement that governs the tone of the eventual Chapter 4 draft and any intermediate
notebook/script output.

### 5. Model A vs. Model B contrast (only when Model B is triggered)

If [analysis/v](../analysis/v_decision_branch.md) selects Branch B, the write-up must explicitly
contrast the two models — not just present both tables and let the reader infer the difference:
- What would a naive reader conclude from Model A's (potentially spurious) static-OLS
  coefficients alone?
- What does Model B's long-run relationship actually show, and does it agree with, weaken, or
  reverse the Model A story?
- Why does the difference matter — tie back to the spurious-regression risk from trending
  regressors (EXR, FDI) that motivated running Model B as the primary model in the first place.

This contrast is produced once, in [b — Model B](b_model_b_ardl_bounds_testing.md) step 9, and
carried into Chapter 4 draft section 6 without being re-derived independently there.

### 6. Deviations from the literal thesis methodology — flag every time, not just once

Per the requirements doc's "Flag deviations" instruction, restate (not just footnote once) each
of the following wherever the relevant output appears:
- `log(FDI)` used in place of raw FDI (Model A and Model B both use `log_fdi`; raw FDI is a
  robustness check only — [analysis/i](../analysis/i_data_preparation.md), step 6).
- Model B / ARDL being estimated **at all** is itself a deviation from the thesis's literal Ch.
  3.5 static-OLS specification — triggered only by the data (mixed I(0)/I(1) result), not
  planned in advance. State this plainly the first time Model B's results are introduced in the
  Chapter 4 draft.
- The 1990–2024 (35-obs) study period vs. the thesis text's stated 1990–2023 (34-obs) scope —
  already governed by [analysis/i](../analysis/i_data_preparation.md), but restate at the top of
  whichever model table uses the 35-obs frame.

### 7. Hypothesis testing basis

- If only Model A is estimated (Branch A): H1/H2 are tested against Model A's coefficients
  directly.
- If Model B is estimated (Branch B): H1/H2 are tested **primarily against Model B's long-run
  coefficients**, with Model B's short-run coefficients and Model A's coefficients reported as
  supplementary/contrastive evidence — not as co-equal bases for accepting/rejecting H1/H2. This
  precedence is set by the requirements doc (§c) and must not be silently reversed even if, say,
  Model A's coefficients happen to look "cleaner."
- A negative-and-significant coefficient on DIVP or DIVM (in whichever model is the primary
  basis) is a genuine finding, not an error to be explained away — report it and flag it for
  discussion against the Ch. 2 product-vs-market diversification debate, per the requirements
  doc.

### 8. Output artifacts

- All code (scripts/notebook) and regression/diagnostic output and charts saved to an outputs
  folder — shared location across both models, not separate per-model folders, so the
  side-by-side comparison table in step vi is easy to assemble from one place.
- Chapter 4 draft is a separate markdown or Word document, written in formal academic thesis
  style consistent with the attached PDF's Chapters 1–3 tone, pulling terminology/variable
  names/citation style from that source rather than introducing new notation.

## Decisions & flags

- This document introduces no new judgment calls of its own — it consolidates conventions
  already settled in the requirements doc (§e "For both models" and the "Additional
  requirements" section) so they are applied consistently rather than re-decided per model.
- If a future addition to [a](a_model_a_static_ols.md) or [b](b_model_b_ardl_bounds_testing.md)
  appears to conflict with a convention stated here, this document is authoritative on
  *reporting/process* conventions; the model-specific documents are authoritative on the
  *estimation* details themselves.

## Definition of done

- Every table produced by either model states its estimation tooling, reports the full
  coefficient/fit-statistic set from requirement 2, and uses the three-tier significance
  convention from requirement 3.
- Reasoning narrative accompanies every step per requirement 4, not just a final results table.
- If Model B is triggered, the explicit Model A vs. Model B contrast (requirement 5) is present
  in both the intermediate output and the Chapter 4 draft.
- All applicable deviations (requirement 6) are restated at each point of use, not stated once
  and assumed carried forward.
- H1/H2 verdicts are drawn from the correct precedence (requirement 7) given which branch was
  taken.
