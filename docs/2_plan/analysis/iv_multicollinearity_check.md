# Plan d.iv — Multicollinearity Check (VIF)

**Parent requirement:** [research_plan.md § d.iv](../../1_requirements/research_plan.md)
**Depends on:** [i — Data preparation](i_data_preparation.md) (uses the same analysis frame;
independent of step iii's result — can run in parallel with stationarity testing)
**Feeds into:** [vi — Estimation](vi_estimation.md) (informs whether any regressor should be
flagged/dropped/reconsidered before estimating Model A/B); reported alongside step iii in the
Chapter 4 diagnostics table

## Objective

Check whether the six regressors {DIVP, DIVM, INF, EXR, log(FDI), SHOCK} are collinear enough
to distort OLS coefficient estimates and inflate standard errors, before those coefficients are
interpreted for H1/H2.

## Inputs

- The 1990–2024 analysis frame from step i, regressor columns only: `divp, divm,
  inflation_rate_pct, exchange_rate, log_fdi, shock` (the dependent variable `eri` is excluded
  from the VIF/correlation calculation — VIF is a regressor-only diagnostic).

## Method / Steps

1. **Compute VIF for each regressor.** For each regressor `Xⱼ`, regress it on all other
   regressors (OLS), take the R² of that auxiliary regression, and compute
   `VIF_j = 1 / (1 − R²_j)`. Use `statsmodels.stats.outliers_influence.variance_inflation_factor`
   or an equivalent manual implementation — note which was used.
   - Include a constant in the design matrix used for VIF (a common EViews-vs-statsmodels
     mismatch: VIF computed without a constant term in the auxiliary regressions gives different
     — usually inflated — numbers). State explicitly whether a constant was included.

2. **Flag any VIF > 10.** Report the full table regardless of outcome (this is a required
   diagnostic table entry even if nothing is flagged). If any VIF exceeds 10, note which
   regressor(s) and by how much, and flag the pair(s) of regressors most likely responsible
   (cross-reference against the correlation matrix in step 3).

3. **Report a plain correlation matrix** of the same six regressors, as an easy manual
   cross-check against EViews (EViews users often eyeball the correlation matrix before trusting
   a VIF number). Highlight any pairwise |r| > 0.8 as a plausible source of any elevated VIF.

4. **Interpret in context.** Given the variable set, the most plausible collinearity risk is
   between `exchange_rate` and `log_fdi` (both trending series, per step ii/iii) — check this
   pair specifically and note the result either way, rather than only reporting the omnibus
   table.

## Formulas

- `VIF_j = 1 / (1 − R²_j)`, where `R²_j` comes from regressing regressor `j` on the remaining
  regressors (+ constant).
- Pearson correlation matrix, standard formula, computed on the same six-column regressor set.

## Decisions & flags

- Whether the VIF auxiliary regressions include a constant — must be stated explicitly since it
  changes the numbers and is a common source of EViews mismatch.
- If VIF > 10 is found for any regressor, this is reported as a finding, not silently acted on
  (e.g., not silently dropping a variable) — the decision of what to do about it (drop, combine,
  re-specify) is deferred to discussion with the user, consistent with the "don't guess on
  judgment calls that change the model materially" instruction in the requirements doc.

## Outputs

- VIF table (CSV): one row per regressor, VIF value, flag column (Y/N for VIF > 10).
- Correlation matrix (CSV + printed table) for the six regressors.

## Definition of done

- VIF computed for all six regressors with the constant-inclusion choice stated.
- Correlation matrix computed and cross-referenced against any elevated VIF.
- Findings reported plainly (flagged or not) — no regressor silently dropped at this stage.
