# Plan d.vii — Post-Estimation Diagnostics

**Parent requirement:** [research_plan.md § d.vii](../../1_requirements/research_plan.md)
**Depends on:** [vi — Estimation](vi_estimation.md) (runs against whichever model(s) were
estimated there)
**Feeds into:** Chapter 4 draft section 2 (diagnostics table); may trigger a re-estimation with
robust standard errors within this same step

## Objective

Validate that the estimated model(s) satisfy the assumptions their standard errors and
significance tests rely on, in the specific order given in the requirements doc, and apply the
Newey-West HAC correction if needed.

## Inputs

- The fitted Model A (OLS) object, and Model B (ARDL/ECM) object if estimated, from step vi.

## Method / Steps, in this order

1. **Autocorrelation.**
   - For Model A (OLS): Durbin-Watson statistic. Report the DW value and interpret against the
     rule-of-thumb bounds (≈2 = no autocorrelation; toward 0 = positive, toward 4 = negative).
   - For Model B (ARDL): use the **Breusch-Godfrey LM test** instead of DW — DW is unreliable
     with a lagged dependent variable, which the ARDL/ECM specification includes by construction.
     Report the LM statistic, degrees of freedom, and p-value; test at a lag order consistent
     with the model's own lag structure (state the lag order chosen).

2. **Heteroskedasticity — Breusch-Pagan test**, for whichever model(s) were estimated. Report the
   LM statistic and p-value; H0 = homoskedastic.

3. **Residual normality — Jarque-Bera test.** Not in the thesis methodology chapter (Ch. 3.7) —
   flag explicitly as an added test, justified as standard practice and trivial to reproduce in
   EViews. Report the JB statistic and p-value; H0 = normally distributed residuals.

4. **Functional form — Ramsey RESET test.** Also not in Ch. 3.7 — flag as an added test with the
   same justification as Jarque-Bera. Report the F-statistic and p-value; H0 = no
   misspecification (typically tested by adding squared/cubed fitted values as auxiliary
   regressors and testing their joint significance).

5. **ARDL-specific diagnostics (only if Model B was estimated):**
   - The bounds-test F-statistic against Pesaran et al. (2001) bounds was already computed in
     step vi as part of estimation — restate it here in the diagnostics table for a complete,
     single-place summary, since conceptually it *is* a pre-condition check before the long-run
     coefficients can be trusted.
   - **CUSUM and CUSUMSQ stability tests**, if feasible given the sample size — check parameter
     stability over the sample period. Report whether the CUSUM/CUSUMSQ lines stay within the 5%
     significance bounds; if infeasible with this sample size (35 observations split across
     ARDL's recursive residual requirements), note why and skip rather than force an unreliable
     result.

6. **Heteroskedasticity/autocorrelation remediation.** If step 1 and/or step 2 detects a problem
   in the **OLS model** (Model A), re-estimate Model A with Newey-West HAC standard errors
   (`statsmodels`' `cov_type="HAC"` with an appropriate `maxlags`, or an equivalent). Report
   **both** the original and HAC-robust standard errors side by side (same coefficients, two SE
   columns) — do not replace one with the other, since the user needs both for the EViews
   comparison. State the `maxlags` choice (a common default is `floor(4*(T/100)^(2/9))`, but with
   T≈35 this rounds to a very small number — state the exact value and formula used).

## Formulas / Statistical detail

- Durbin-Watson: `DW = Σ(eₜ − eₜ₋₁)² / Σeₜ²`.
- Breusch-Godfrey LM: regress residuals on lagged residuals + original regressors; `LM =
  n·R²` from that auxiliary regression, χ² distributed with df = number of lags tested.
- Breusch-Pagan: regress squared residuals on the regressors; `LM = n·R²` from that auxiliary
  regression, χ² distributed with df = number of regressors.
- Jarque-Bera: `JB = (n/6)·(S² + (K−3)²/4)`, where S = skewness, K = kurtosis of residuals; χ²
  distributed with 2 df.
- Ramsey RESET: augment the original regression with powers of the fitted values (ŷ², ŷ³, …),
  test their joint significance via an F-test.
- Newey-West HAC standard errors: heteroskedasticity-and-autocorrelation-consistent covariance
  matrix, `maxlags` truncation parameter as stated above.

## Decisions & flags

- Jarque-Bera and RESET are explicitly flagged as additions beyond the literal Ch. 3.7 spec —
  state this in the write-up each time these results are presented, not just once in passing.
- CUSUM/CUSUMSQ are attempted but conditionally skipped if infeasible given the sample size —
  this is a data-driven judgment call to flag, not silently omit.
- The Newey-West `maxlags` value is a judgment call with a stated formula-based default —
  document the exact number used given T≈35, so the user can replicate or override it in EViews.
- Diagnostics are run on **all** estimated models from step vi (Model A always; Model B and the
  first-differenced OLS if Branch B applies) — state which diagnostics apply to which model,
  since DW/Breusch-Godfrey in particular are model-specific, not universal.

## Outputs

- One diagnostics results table per model, in the exact sequence run (autocorrelation →
  heteroskedasticity → normality → functional form → [ARDL-specific] → HAC remediation if
  triggered), each row: test name, statistic, p-value, plain-language interpretation.
- If HAC remediation was triggered: a side-by-side original-SE vs. HAC-SE coefficient table.

## Definition of done

- All five (or six, if ARDL) diagnostic tests run in the specified order, on every model
  estimated in step vi.
- Each test's statistic, p-value, and plain-language interpretation reported.
- HAC re-estimation performed and reported side-by-side if triggered by steps 1–2; explicitly
  noted as not triggered if diagnostics come back clean.
