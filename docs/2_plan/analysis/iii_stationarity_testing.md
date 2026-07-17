# Plan d.iii — Stationarity Testing (Augmented Dickey-Fuller)

**Parent requirement:** [research_plan.md § d.iii](../../1_requirements/research_plan.md)
**Depends on:** [i — Data preparation](i_data_preparation.md)
**Feeds into:** [iv — Multicollinearity check](iv_multicollinearity_check.md) (runs in parallel,
no dependency on this step's result), and critically [v — Decision branch](v_decision_branch.md),
which reads this step's output to choose the modeling path

## Objective

Determine the order of integration — I(0), I(1), or I(2) — of all six model variables, since
this single result decides whether Model A (static OLS) alone is valid, or whether Model B
(ARDL bounds testing) must be estimated as the primary model. This is the most consequential
diagnostic step in the whole pipeline.

## Inputs

- The 1990–2024 analysis frame from step i, specifically: `eri, divp, divm,
  inflation_rate_pct, exchange_rate, log_fdi` (six variables — note `log_fdi`, not raw FDI, per
  the step i deviation; `shock` is a dummy and is not tested for stationarity).

## Method / Steps

1. **Run ADF at level, for each of the six variables.** For each series:
   - Choose the ADF specification (constant only vs. constant + trend) by first inspecting the
     series plot from step ii — a series with a visible trend (expected for `exchange_rate` and
     `log_fdi`) should be tested with a trend term included; a series without an obvious trend
     (ERI, PDI, MDI, INF) tested with a constant only. State the specification chosen per
     variable explicitly, since this choice affects the critical values and is a common
     EViews-vs-Python mismatch point if not documented.
   - Choose lag length via AIC-based automatic selection (`statsmodels.tsa.stattools.adfuller`
     with `autolag="AIC"`), given the very short series (35 observations) — report the selected
     lag per variable.
   - Report: ADF test statistic, p-value, MacKinnon critical values at 1%/5%/10%, and the
     selected lag length.
   - Conclusion: stationary at level (reject H0: unit root, at 5%) → I(0); otherwise → not
     stationary at level, proceed to first-differencing.

2. **Run ADF on the first difference, for every variable that failed the level test.** This
   confirms I(1) (stationary after one differencing) and — critically — rules out I(2). Use the
   same lag-selection and trend/constant logic, but a first-differenced series should almost
   never need a trend term (differencing removes a linear trend), so default to constant-only
   here unless the differenced series still visibly trends.

3. **Run ADF on the second difference only if a variable is still non-stationary after the first
   difference.** This is the check for I(2). If any variable requires a second difference to
   become stationary, this triggers the **stop-and-report** branch in step v (ARDL bounds testing
   is invalid with I(2) regressors) — do not proceed past this point for that variable without
   flagging it back to the user first.

4. **Assemble the results table.** One row per variable × per test level (level, 1st diff, and
   2nd diff only if run), columns: variable, specification (constant/trend), lag, ADF stat,
   p-value, 1%/5%/10% critical values, conclusion (stationary/non-stationary), and a final
   "order of integration" column (I(0)/I(1)/I(2)) once all levels have been tested for that
   variable.

## Formulas / Statistical detail

- ADF test regression (constant + trend form):
  `Δyₜ = α + βt + γyₜ₋₁ + Σᵢ δᵢ Δyₜ₋ᵢ + εₜ`
  H0: γ = 0 (unit root, non-stationary). Reject H0 if the ADF t-statistic is more negative than
  the MacKinnon critical value at the chosen significance level.
- First difference: `Δyₜ = yₜ − yₜ₋₁`; second difference: `Δ²yₜ = Δyₜ − Δyₜ₋₁`.

## Decisions & flags

- **Trend-vs-constant specification per variable** is a judgment call informed by step ii's
  plots. State the default used per variable (expected: trend for `exchange_rate` and
  `log_fdi`, constant-only for `eri, divp, divm, inflation_rate_pct`) and note that EViews'
  default ADF dialog requires the same choice to be made manually, so this must be documented
  precisely for the user's cross-check.
- **Any I(2) result stops the pipeline** at this step — per the requirements doc, this is not a
  silent judgment call; report back immediately with which variable(s) are I(2) before
  continuing to step iv onward, since I(2) changes the whole modeling approach (e.g., further
  differencing or dropping/transforming that variable) and is explicitly out of scope for this
  plan to resolve unilaterally.
- With only 35 (or 34) observations, ADF has low power to reject a false unit-root null — note
  this caveat in the write-up regardless of outcome, since it affects how confidently I(0) vs
  I(1) conclusions should be stated.

## Outputs

- ADF results table (CSV), covering level and first-difference (and second-difference if
  triggered) tests for all six variables.
- A one-paragraph plain-language conclusion per variable ("X is I(1) — non-stationary at level,
  stationary after first differencing") feeding directly into step v's decision.

## Definition of done

- All six variables tested at level.
- Every variable that failed the level test re-tested at first difference.
- Second-difference test run for any variable still non-stationary after first-differencing,
  with an explicit stop-and-flag if any I(2) result is found.
- Final order-of-integration classification recorded for all six variables, ready to be handed
  to step v's decision branch.
