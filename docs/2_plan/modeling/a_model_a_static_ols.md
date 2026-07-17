# Plan e.A — Model A: Static OLS (Literal-Thesis Specification)

**Parent requirement:** [research_plan.md § e — Model A](../../1_requirements/research_plan.md)
**Depends on:** [analysis/i — Data preparation](../analysis/i_data_preparation.md) for the
analysis frame
**Independent of:** the branch outcome in [analysis/v — Decision branch](../analysis/v_decision_branch.md)
— Model A is estimated **unconditionally**, regardless of what stationarity testing finds
**Feeds into:** [analysis/vi — Estimation](../analysis/vi_estimation.md) (executes this
specification as its "Model A" section); [analysis/vii — Post-estimation diagnostics](../analysis/vii_post_estimation_diagnostics.md);
[c — Shared cross-model requirements](c_shared_requirements_for_both_models.md); Chapter 4 draft
section 3

## Objective

Specify Model A exactly as written in the thesis's methodology chapter (Ch. 3.5, Eq. 3.1), and
estimate it as the fixed baseline that every other result in this project — Model B if triggered,
the EViews cross-check, and the "what would a naive reader conclude" narrative — is compared
against. This document is the specification; [analysis/vi_estimation.md](../analysis/vi_estimation.md)
is the execution checklist that runs it. If the two ever appear to disagree, this file and the
requirements doc are authoritative on *what* the model is; vi_estimation.md is authoritative on
*when in the pipeline* it runs.

## Model specification

```
ERI = β0 + β1·DIVP + β2·DIVM + β3·INF + β4·EXR + β5·log(FDI) + β6·SHOCK + ε
```

| Symbol | Variable | Column in analysis frame | Role | Hypothesis | Expected sign |
|---|---|---|---|---|---|
| ERI | Economic Resilience Index | `eri` | Dependent | — | — |
| DIVP | Product diversification (HHI-based) | `divp` | Regressor | H1 | + |
| DIVM | Market diversification (HHI-based) | `divm` | Regressor | H2 | + |
| INF | Inflation rate | `inflation_rate_pct` | Control | — | ambiguous a priori |
| EXR | Exchange rate (LKR/USD) | `exchange_rate` | Control | — | ambiguous a priori |
| log(FDI) | Log of FDI net inflows | `log_fdi` | Control | — | + (theory: FDI supports resilience) |
| SHOCK | Crisis-year dummy (2008, 2009, 2020–22) | `shock` | Control | — | − |

- Estimated on the full 1990–2024 analysis frame (N = 35), with a constant.
- `log_fdi`, not raw FDI, is used here per the step-i deviation (flag this explicitly wherever
  Model A results are reported — see [c — Shared requirements](c_shared_requirements_for_both_models.md)).
  The raw-FDI version is a separate robustness check ([analysis/viii](../analysis/viii_robustness_checks.md)),
  not a substitute for this specification.

## Method / Steps

1. Confirm the 1990–2024 analysis frame from step i is available with all seven columns above.
2. Estimate via `statsmodels.api.OLS` (with `sm.add_constant`). Note this explicitly in the
   output — it is the exact function the user cross-checks against EViews' `LS` command.
3. Report the full summary table: coefficient, standard error, t-statistic, p-value per
   regressor; R², adjusted R², F-statistic and its p-value; N.
4. Apply significance stars at the 1%/5%/10% levels (`***`/`**`/`*`).
5. Interpret each coefficient's sign, magnitude, and significance directly against H1 (β₁,
   DIVP) and H2 (β₂, DIVM) — state whether each hypothesis is supported, rejected, or ambiguous
   at this stage, and translate the coefficient into economic-significance language (e.g. "a 0.1
   increase in DIVP is associated with a Δ ERI of X, holding other variables constant").
6. Report this model **unconditionally** — it is estimated and shown in the write-up whether
   analysis/v selects Branch A, B, or halts at Branch C for a different regressor. It is the
   fixed anchor for every comparison in this project.
7. **Conditional validity caveat.** If [analysis/iii — Stationarity testing](../analysis/iii_stationarity_testing.md)
   finds any I(1) regressor (the expected Branch B outcome given EXR's and FDI's visible
   trends), attach this caveat directly alongside Model A's coefficient table: estimates here
   may reflect a **spurious regression** — significant coefficients driven by shared trends
   across non-stationary series rather than a genuine relationship — and should not be treated
   as the primary basis for H1/H2 until compared against Model B's long-run coefficients. Do not
   omit this caveat even though the numbers themselves are still reported in full.

## Formulas

- OLS estimator: `β̂ = (X'X)⁻¹X'y`.
- Standard errors, t-statistics, R², adjusted R², and F-statistic: standard OLS formulas as
  implemented by `statsmodels.api.OLS`.

## Decisions & flags

- Model A is always estimated — this is settled in the requirements doc, not a judgment call
  made here.
- The spurious-regression caveat in step 7 is conditional on analysis/iii's/v's output; state it
  when applicable, omit it (without silently deleting the requirement) if all six variables test
  I(0) and Branch A is taken.
- `log_fdi` vs. raw FDI: this specification uses `log_fdi` (flagged deviation, justified in step
  i); raw FDI is a robustness check only, never substituted into this primary specification.

## Outputs

- Model A regression summary table (CSV + printed), significance-starred.
- A short interpretation paragraph, explicitly tied to H1/H2, usable directly in Chapter 4 draft
  section 3 and section 5.
- The spurious-regression caveat text, if triggered, attached to the same table.

## Definition of done

- Model A estimated on the full 35-obs frame with `statsmodels.api.OLS`, constant included.
- Full summary table reported with significance stars at 1%/5%/10%.
- Coefficients interpreted against H1/H2 in both statistical and economic-significance terms.
- Reported regardless of the analysis/v branch outcome; spurious-regression caveat attached
  whenever any regressor tested I(1).
