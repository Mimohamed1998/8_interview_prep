# Plan d.vi — Estimation

**Parent requirement:** [research_plan.md § d.vi](../../1_requirements/research_plan.md), per
the model specifications in [research_plan.md § e](../../1_requirements/research_plan.md)
**Depends on:** [v — Decision branch](v_decision_branch.md) (determines which model(s) below are
estimated); [i — Data preparation](i_data_preparation.md) for the analysis frame
**Feeds into:** [vii — Post-estimation diagnostics](vii_post_estimation_diagnostics.md)
(diagnostics run on whichever model(s) are estimated here); Chapter 4 draft sections 3–4

## Objective

Estimate the model(s) selected by step v's decision branch, always including Model A (static
OLS) as the literal-thesis baseline, and Model B (ARDL bounds testing) if Branch B was triggered.

## Inputs

- The 1990–2024 analysis frame from step i.
- The branch decision from step v (A, B, or halted at C).

## Method / Steps

### Model A — Static OLS (always estimated, regardless of branch)

```
ERI = β0 + β1·DIVP + β2·DIVM + β3·INF + β4·EXR + β5·log(FDI) + β6·SHOCK + ε
```

1. Estimate via `statsmodels.api.OLS` on the full 1990–2024 sample (35 obs), with a constant.
2. Report the full summary table: coefficients, standard errors, t-statistics, p-values, R²,
   adjusted R², F-statistic and its p-value, N.
3. Apply significance stars at 1%/5%/10% (***/**/*).
4. Note explicitly which package/function was used (`statsmodels.api.OLS`), since this is what
   the user cross-checks against EViews' `LS` output.
5. This model is the baseline regardless of the ADF outcome — even if Branch B is triggered,
   Model A is still reported (as the "what a naive reader would conclude" comparison point).

### Model B — ARDL(p,q) bounds testing (only if step v selected Branch B)

Conditional Error-Correction (ECM) form:

```
ΔERI_t = α0 + Σγᵢ·ΔERI_(t-i) + Σδⱼ·ΔX_(t-j) + θ1·ERI_(t-1) + θ2·DIVP_(t-1) + θ3·DIVM_(t-1)
         + θ4·INF_(t-1) + θ5·EXR_(t-1) + θ6·log(FDI)_(t-1) + θ7·SHOCK_(t-1) + ε_t
```
where X = {DIVP, DIVM, INF, EXR, log(FDI), SHOCK}.

1. **Lag selection.** Search lag combinations for `p` (own lags of ERI) and `q` (lags of each
   regressor), with a **maximum lag of 1–2** given the ~34–35 observation sample (protecting
   degrees of freedom). Select the optimal `(p,q)` via AIC; report BIC alongside for comparison.
   If AIC and BIC disagree on the optimal lag, **flag this explicitly rather than silently
   picking one** — state which default is used (AIC, as the requirements doc's stated default)
   and note the BIC-implied alternative so the user can override it. This exact scenario is also
   revisited as a robustness check in step viii.
2. **Estimate the ARDL/ECM model** via `statsmodels.tsa.ardl.ARDL` (or an equivalent
   bounds-testing implementation) at the selected `(p,q)`. Note explicitly which
   package/function was used, since EViews' built-in ARDL wizard is what the user cross-checks
   against.
3. **Bounds F-test.** Test the joint significance of the lagged-level terms (θ1…θ7) against
   Pesaran, Shin & Smith (2001) critical value bounds (using k = 6 regressors). Report the
   F-statistic and where it falls:
   - Above the upper bound → cointegration confirmed → long-run relationship exists, long-run
     coefficients are interpretable → proceed to step 4.
   - Below the lower bound → no cointegration → fall back to reporting the differenced-OLS
     model / ARDL short-run-only interpretation; do not report long-run coefficients as if
     cointegration were confirmed.
   - Between the bounds → inconclusive; report as such explicitly, do not force a conclusion
     either way.
4. **Long-run coefficients** (only if cointegration confirmed): derive as `long-run β = −θₖ/θ1`
   for each regressor `k`. Report alongside standard errors (via the delta method or bootstrap —
   note which is used) and significance stars.
5. **Error-correction term.** Report θ1 (the ERI_(t-1) coefficient) itself — this should be
   negative and significant, ideally between −1 and 0. Its magnitude is the speed of adjustment
   back to the long-run resilience level after a shock (directly relevant to the "restorative
   capacity" framing in Ch. 2.3). Flag if θ1 is not negative-and-significant, since that would
   undermine the cointegration story.
6. **Short-run coefficients.** Report all Δ-term coefficients (γᵢ, δⱼ) as supplementary evidence
   on short-run dynamics and adjustment speed.

### Also estimated for comparison if Branch B is triggered

Per the requirements doc, when Branch B applies, also estimate and report side by side with
Model A and Model B:
- **OLS on first-differenced variables** (`ΔERI = β0 + β1·ΔDIVP + β2·ΔDIVM + β3·ΔINF +
  β4·ΔEXR + β5·Δlog(FDI) + β6·ΔSHOCK + ε`) — shows what changes once the trending-regressor
  spurious-regression risk is removed, without imposing the full ARDL/ECM structure.

## Formulas

- OLS: `β̂ = (X'X)⁻¹X'y`.
- ARDL bounds F-test: joint Wald test of `H0: θ1 = θ2 = … = θ7 = 0` in the ECM equation above,
  compared against Pesaran et al. (2001) Table CI(iii) critical value bounds for k=6 regressors,
  case with unrestricted intercept and no trend (confirm this is the correct case given the
  model's inclusion of a constant and no explicit trend term — state which case is used).
- Long-run coefficient: `βₖ_LR = −θₖ / θ1`.

## Decisions & flags

- ARDL max lag capped at 1–2 given the small sample — stated default; AIC used as the tiebreaker
  if AIC/BIC disagree, with the BIC alternative reported for the user to override.
- Pesaran et al. (2001) critical-value "case" (intercept/trend assumptions) used for the bounds
  test must be stated explicitly, since picking the wrong case is a common source of
  EViews-vs-Python mismatch.
- If the bounds test result is inconclusive (between bounds), this is reported as such — not
  forced toward either conclusion.
- If θ1 (error-correction term) is not negative-and-significant even though the bounds test
  confirms cointegration, flag this as an internal inconsistency worth discussing rather than
  silently reporting the long-run coefficients as if nothing were wrong.

## Outputs

- Model A full regression summary table (CSV + printed).
- Model B (if applicable): lag-selection table (AIC/BIC by candidate lag), bounds F-test result
  table, long-run coefficient table, error-correction term, short-run coefficient table.
- First-differenced OLS table (if Branch B applies).
- All three (or one, if Branch A) tables assembled into the side-by-side comparison table
  described in the requirements doc.

## Definition of done

- Model A estimated and fully reported regardless of branch.
- If Branch B: ARDL/ECM estimated with lag selection, bounds test, long-run coefficients,
  error-correction term, and short-run coefficients all reported, plus the first-differenced OLS
  comparison.
- Every judgment call flagged in this plan (lag tiebreak, bounds-test case, inconclusive bounds
  result) is stated explicitly in the output, not silently resolved.
