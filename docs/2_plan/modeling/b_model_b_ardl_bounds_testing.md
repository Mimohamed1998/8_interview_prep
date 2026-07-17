# Plan e.B — Model B: ARDL(p,q) Bounds Testing

**Parent requirement:** [research_plan.md § e — Model B](../../1_requirements/research_plan.md)
**Depends on:** [analysis/v — Decision branch](../analysis/v_decision_branch.md) — this model is
estimated **only if** Branch B is triggered (mixed I(0)/I(1) regressors, no I(2));
[analysis/i — Data preparation](../analysis/i_data_preparation.md) for the analysis frame
**Feeds into:** [analysis/vi — Estimation](../analysis/vi_estimation.md) (executes this
specification as its "Model B" section); [analysis/vii — Post-estimation diagnostics](../analysis/vii_post_estimation_diagnostics.md)
(bounds-test restatement, Breusch-Godfrey, CUSUM/CUSUMSQ); [analysis/viii — Robustness checks](../analysis/viii_robustness_checks.md)
(becomes the "primary model" re-estimated under alternate conditions); Chapter 4 draft section 4

## Objective

Specify the ARDL(p,q) bounds-testing model that becomes the **primary model for inference** if
stationarity testing (step d.iii) shows a mix of I(0)/I(1) regressors with no I(2) variable. This
is the project's substantive answer to the spurious-regression risk in Model A: rather than
choosing between under-fitting (OLS on levels, ignoring non-stationarity) or over-fitting (a
Johansen VECM the ~35-observation sample cannot support), ARDL bounds testing (Pesaran, Shin &
Smith, 2001) estimates short-run dynamics and a long-run cointegrating relationship in one
step, and remains valid regardless of whether individual regressors are I(0) or I(1). This
document is the specification; [analysis/vi_estimation.md](../analysis/vi_estimation.md) is the
execution checklist that runs it, and [c — Shared cross-model requirements](c_shared_requirements_for_both_models.md)
governs conventions common to both Model A and Model B.

## Trigger condition

- Estimated **only if** [analysis/v](../analysis/v_decision_branch.md) records Branch B.
- If Branch A (all six variables I(0)) is taken instead, this model is **not** estimated —
  static OLS on levels is the sufficient single model per the requirements doc, and this
  document's contents are not applicable to the Chapter 4 draft for that run.
- If Branch C (any I(2) variable) is taken, estimation halts before this step entirely — see
  [analysis/v](../analysis/v_decision_branch.md) for the stop-and-flag procedure.

## Model specification

Conditional Error-Correction (ECM) form of the ARDL(p,q) model:

```
ΔERI_t = α0 + Σγᵢ·ΔERI_(t-i) + Σδⱼ·ΔX_(t-j) + θ1·ERI_(t-1) + θ2·DIVP_(t-1) + θ3·DIVM_(t-1)
         + θ4·INF_(t-1) + θ5·EXR_(t-1) + θ6·log(FDI)_(t-1) + θ7·SHOCK_(t-1) + ε_t
```

where `X = {DIVP, DIVM, INF, EXR, log(FDI), SHOCK}`.

| Symbol | Role | Interpretation |
|---|---|---|
| `α0` | Constant | ECM intercept |
| `γᵢ` (i = 1…p) | Short-run coefficients on lagged `ΔERI` | Own-dynamics adjustment |
| `δⱼ` (j = 0…q, per regressor) | Short-run coefficients on lagged `ΔX` | Short-run effects |
| `θ1` | Coefficient on `ERI_(t-1)` | **Error-correction term** — speed of adjustment to long-run equilibrium; expected negative, between −1 and 0 |
| `θ2…θ7` | Coefficients on lagged levels of `DIVP, DIVM, INF, EXR, log(FDI), SHOCK` | Used to derive long-run coefficients: `βₖ_LR = −θₖ/θ1` |

- Same six regressors and same dependent variable as Model A — no new variables are introduced;
  only the functional form (differenced + one-period lagged levels) differs.
- Same variable roles/hypotheses/expected signs as documented in
  [a — Model A](a_model_a_static_ols.md)'s specification table, but tested here against the
  **long-run** derived coefficients (`βₖ_LR`), not the raw `θ` estimates directly.

## Method / Steps

1. **Confirm trigger.** Verify [analysis/v](../analysis/v_decision_branch.md) recorded Branch B
   before proceeding; if not, this model is skipped entirely (see Trigger condition above).

2. **Lag selection.** Search candidate `(p,q)` combinations — `p` = own lags of `ERI`, `q` =
   lags of each regressor in `X` — with a **maximum lag of 1–2**, given the ~34–35 observation
   sample (protecting degrees of freedom is the binding constraint here, not model fit). Select
   the optimal `(p,q)` by AIC; report BIC alongside for every candidate combination, not just the
   winner.
   - **If AIC and BIC agree** on the optimal `(p,q)`, use it without further comment.
   - **If AIC and BIC disagree**, flag this explicitly rather than silently picking one: state
     that AIC is used as the default (per the requirements doc's stated default), report the
     BIC-implied alternative lag, and note this is a judgment call the user can override. This
     scenario is revisited directly in the robustness checks
     ([analysis/viii](../analysis/viii_robustness_checks.md), check 4).

3. **Estimate the ARDL/ECM model** at the selected `(p,q)` via `statsmodels.tsa.ardl.ARDL` (or
   an equivalent bounds-testing implementation, e.g. constructing the conditional ECM manually
   via `statsmodels.api.OLS` on differenced/lagged series if the ARDL module's bounds-test
   output is insufficient). State explicitly which package/function and which specific API call
   was used, since EViews' built-in ARDL wizard is what every coefficient here is cross-checked
   against, and small implementation differences (e.g. how the intercept/trend case is handled)
   are the most likely source of a Python-vs-EViews mismatch.

4. **Bounds F-test for cointegration.** Test the joint null `H0: θ1 = θ2 = … = θ7 = 0` (no
   long-run relationship) via an F-test on the lagged-level terms, against Pesaran, Shin & Smith
   (2001) critical value bounds for `k = 6` regressors. State explicitly which "case" (I–V, per
   Pesaran et al.'s intercept/trend typology) is used — this specification includes an
   unrestricted intercept and no trend, so confirm Case III (or the applicable case) is the one
   applied, since picking the wrong case is a common source of EViews-vs-Python mismatch.
   - **F-stat above the upper bound** → cointegration confirmed → long-run relationship exists →
     proceed to step 5.
   - **F-stat below the lower bound** → no cointegration → do not report long-run coefficients as
     if confirmed; fall back to the short-run/differenced-OLS interpretation only, and say so
     explicitly in the write-up.
   - **F-stat between the bounds** → inconclusive → report as such; do not force a conclusion
     either way.

5. **Long-run coefficients** (only if cointegration confirmed in step 4). Derive
   `βₖ_LR = −θₖ/θ1` for each of the six regressors. Report standard errors for these derived
   coefficients via the delta method (or bootstrap, if the delta method is not directly available
   from the fitted object) — state explicitly which method is used, since long-run SEs are not a
   direct output of the ECM regression and this is another likely EViews mismatch point. Apply
   significance stars at 1%/5%/10% to the long-run coefficients.

6. **Error-correction term.** Report `θ1` (the `ERI_(t-1)` coefficient) on its own, with its
   standard error, t-statistic, and p-value. Expected: negative and significant, ideally between
   −1 and 0 — this is the speed of adjustment back to the long-run resilience level after a
   deviation (e.g., a shock), directly relevant to the thesis's "restorative capacity" framing
   (Ch. 2.3, Briguglio et al. 2009). If `θ1` is not negative-and-significant even though step 4
   confirmed cointegration, flag this explicitly as an internal inconsistency worth discussing,
   rather than silently reporting the long-run coefficients as if nothing were wrong.

7. **Short-run coefficients.** Report all `γᵢ` (lagged `ΔERI`) and `δⱼ` (lagged `ΔX`, per
   regressor) coefficients, with standard errors, t-statistics, p-values, and significance stars,
   as supplementary evidence on short-run dynamics and adjustment speed — per the requirements
   doc, H1/H2 are tested primarily against the long-run coefficients (step 5), with these
   short-run terms reported alongside as secondary evidence, not as the primary basis for
   accepting/rejecting H1/H2.

8. **Interpret against H1/H2.** Using the long-run coefficients from step 5 (primary) and the
   short-run coefficients from step 7 (supplementary): state whether H1 (`DIVP` long-run
   coefficient positive and significant) and H2 (`DIVM` long-run coefficient positive and
   significant) are supported, rejected, or ambiguous. Translate into economic-significance
   language (e.g., "a 0.1 increase in the long-run DIVP coefficient's implied effect is a Δ ERI
   of X in the long run, holding other variables constant").

9. **Contrast against Model A.** Explicitly state what a naive reader would conclude from Model
   A's (potentially spurious) static-OLS coefficients versus what Model B's long-run
   relationship actually shows — same sign and magnitude, or materially different? This
   contrast is required by the requirements doc whenever Model B is triggered, and belongs in
   both this output and the Chapter 4 draft narrative (see
   [c — Shared cross-model requirements](c_shared_requirements_for_both_models.md)).

## Also estimated for comparison (required whenever Model B is triggered)

Per the requirements doc, when Branch B applies, also estimate and report side by side with
Model A and Model B:

- **OLS on first-differenced variables**:
  `ΔERI = β0 + β1·ΔDIVP + β2·ΔDIVM + β3·ΔINF + β4·ΔEXR + β5·Δlog(FDI) + β6·ΔSHOCK + ε`
  This shows what changes once the trending-regressor spurious-regression risk is removed by
  differencing, without imposing the full ARDL/ECM long-run structure — a middle point between
  Model A (levels) and Model B (levels + differences combined).

This is not a fourth "model" in its own right for H1/H2 purposes — it is a diagnostic
comparison point, reported alongside Models A and B in the three-way side-by-side table.

## Formulas

- ARDL bounds F-test: joint Wald test of `H0: θ1 = θ2 = … = θ7 = 0` in the ECM equation above,
  compared against Pesaran et al. (2001) critical value bounds, Case III (unrestricted
  intercept, no trend) for `k = 6` — confirm this case matches the model's actual constant/trend
  specification before citing the bounds table.
- Long-run coefficient: `βₖ_LR = −θₖ / θ1`.
- Long-run coefficient standard error: delta method (or bootstrap) applied to `−θₖ/θ1`, given
  `Var(θₖ)`, `Var(θ1)`, and `Cov(θₖ, θ1)` from the ECM's coefficient covariance matrix.
- AIC/BIC for lag selection: standard information-criterion formulas as computed by
  `statsmodels.tsa.ardl.ardl_select_order` (or equivalent), evaluated over the candidate
  `(p,q)` grid described in step 2.

## Decisions & flags

- Trigger condition (Branch B only) is settled by [analysis/v](../analysis/v_decision_branch.md)
  — not re-decided here.
- Max lag capped at 1–2 given the small sample — stated default; flag rather than silently
  extend if a longer lag is later found necessary.
- AIC used as the lag-selection tiebreaker if AIC/BIC disagree, with the BIC alternative
  reported for the user to override — per requirements doc's "don't guess" instruction on
  materially model-changing choices.
- Pesaran et al. (2001) critical-value case (I–V) used for the bounds test must be stated
  explicitly — a common EViews-vs-Python mismatch source.
- If the bounds test is inconclusive (between bounds), report as such, not forced toward either
  conclusion — this is itself a reportable finding, not a modeling failure to paper over.
- If `θ1` is not negative-and-significant despite confirmed cointegration, flag as an internal
  inconsistency for discussion rather than silently proceeding.
- Delta-method vs. bootstrap for long-run coefficient SEs is a judgment call — state which is
  used and why (delta method preferred as the standard/EViews-comparable default unless sample
  size or nonlinearity makes it unreliable).

## Outputs

- Lag-selection table: AIC and BIC by candidate `(p,q)`, selected lag highlighted, tiebreak note
  if applicable.
- Bounds F-test result: F-statistic, critical value bounds (case stated), and conclusion
  (cointegration confirmed / not confirmed / inconclusive).
- Long-run coefficient table: coefficient, SE (method stated), t-stat, p-value, significance
  stars, per regressor.
- Error-correction term (`θ1`): coefficient, SE, t-stat, p-value, plain-language speed-of-adjustment
  interpretation.
- Short-run coefficient table: all `γᵢ`, `δⱼ` terms with SEs, t-stats, p-values, significance
  stars.
- First-differenced OLS comparison table (required alongside, per requirements doc).
- Interpretation paragraph tied explicitly to H1/H2, usable directly in Chapter 4 draft section
  4 and section 5.
- The Model A vs. Model B contrast paragraph (step 9), usable in Chapter 4 draft section 6.

## Definition of done

- Trigger condition confirmed (Branch B) before any estimation in this document proceeds.
- Lag selection performed with AIC/BIC reported for all candidates and any disagreement flagged.
- ARDL/ECM estimated with stated package/function and stated bounds-test case.
- Bounds F-test run and its three-way outcome (confirmed/not confirmed/inconclusive) reported
  without being forced.
- If cointegration confirmed: long-run coefficients, their SEs (method stated), and the
  error-correction term all reported and interpreted against H1/H2.
- Short-run coefficients reported as supplementary evidence.
- First-differenced OLS comparison estimated and reported alongside.
- Model A vs. Model B contrast explicitly written out, not left implicit in the numbers alone.
