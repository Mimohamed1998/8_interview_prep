# Plan d.v — Decision Branch (Modeling Path Selection)

**Parent requirement:** [research_plan.md § d.v](../../1_requirements/research_plan.md)
**Depends on:** [iii — Stationarity testing](iii_stationarity_testing.md) (the sole input to
this decision); informed contextually by [iv — Multicollinearity check](iv_multicollinearity_check.md)
**Feeds into:** [vi — Estimation](vi_estimation.md) (determines which model(s) are estimated
there)

## Objective

This step is a documented decision memo, not a computation — it takes the order-of-integration
classification produced in step iii and applies the three-way branch rule from the requirements
doc to determine the modeling path. Writing it as its own plan/output ensures the decision is
explicit, auditable, and made *before* any estimation happens, rather than being an implicit
byproduct of the estimation step.

## Inputs

- The final order-of-integration table from step iii: one classification (I(0), I(1), or I(2))
  per variable, for `ERI, DIVP, DIVM, INF, EXR, log(FDI)`.

## Method / Steps

1. **Read the six classifications from step iii.**

2. **Apply the branch rule, exactly as specified:**
   - **Branch A — all six I(0):** Proceed with static OLS on levels only (Ch. 3.5, Eq. 3.1) as
     the single, sufficient model. No ARDL needed.
   - **Branch B — mixed I(0)/I(1), no I(2):** This is the branch anticipated in the requirements
     doc given the visible trends in EXR and FDI. Estimate ARDL(p,q) bounds testing as the
     **primary model**. Still estimate, for comparison: (a) the literal-thesis static OLS on
     levels, and (b) OLS on first-differenced variables. All three are presented side by side in
     the Chapter 4 write-up.
   - **Branch C — any variable I(2):** Do not proceed with ARDL (bounds testing is invalid with
     an I(2) regressor). Stop here. Report back which variable(s) are I(2) and that a different
     approach is required (e.g., further differencing, or dropping/transforming that variable)
     before any estimation step (vi) can proceed. This is an explicit "don't guess" stop point
     per the requirements doc — do not unilaterally decide how to handle the I(2) variable.

3. **Record which branch was taken and why**, quoting the specific I(0)/I(1)/I(2) result per
   variable that triggered it. This record is what step vi reads to know which models to
   estimate, and it's also the first paragraph of the diagnostics section in the Chapter 4 draft
   (readers need to see *why* ARDL was chosen over static OLS, not just the final numbers).

4. **If Branch B is taken**, additionally note here (for step vi to pick up) which specific
   variables are I(1) — these are the ones driving the spurious-regression risk in Model A and
   the ones whose long-run coefficients are meaningful in Model B.

## Decisions & flags

- This step makes **no new judgment calls** of its own beyond applying the pre-agreed rule — the
  rule itself, and the default action for each branch, is already settled in the requirements
  doc. The only thing this step does is apply it transparently and stop-and-flag if Branch C is
  triggered.
- If Branch C triggers, this plan explicitly does **not** prescribe a fix (e.g., which
  differencing or transformation to use) — that is a materially model-changing judgment call
  that must be put to the user per the requirements doc's "don't guess" instruction.

## Outputs

- A short decision memo (a few sentences to a paragraph): which branch was taken, the
  per-variable I(0)/I(1)/I(2) classifications that drove it, and (if Branch B) which models will
  be estimated in step vi.

## Definition of done

- Branch determined from step iii's results and recorded with justification.
- If Branch C, pipeline explicitly halted before step vi with the I(2) variable(s) flagged back
  to the user — no silent workaround applied.
- If Branch A or B, step vi has a clear, unambiguous instruction on which model(s) to estimate.
