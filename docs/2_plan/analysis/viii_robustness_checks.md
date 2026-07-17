# Plan d.viii — Robustness Checks

**Parent requirement:** [research_plan.md § d.viii](../../1_requirements/research_plan.md)
**Depends on:** [vi — Estimation](vi_estimation.md) (re-estimates the primary model under
alternate conditions), [i — Data preparation](i_data_preparation.md) (uses the 1990–2023 subset
and raw-FDI columns already prepared there)
**Feeds into:** Chapter 4 draft section 7 (robustness summary); directly supports or undermines
confidence in H1/H2 alongside section 5's interpretation

## Objective

Re-estimate the primary model (Model B/ARDL if Branch B was selected in step v; Model A/OLS
otherwise) under four alternate conditions, and report how much the DIVP/DIVM coefficients move
— this is the evidentiary basis for how much confidence to place in H1/H2.

## Inputs

- The primary model specification and fitted result from step vi.
- The 1990–2023 subset (34 obs) prepared in step i.
- Both the log(FDI) and raw-FDI columns from step i.

## Method / Steps

Re-estimate the **primary model** (whichever step v selected) under each of the following four
conditions, one at a time (i.e., changing one thing per check, not stacking all four together
initially — a stacked "kitchen sink" version can optionally be added at the end as a fifth,
clearly-labeled check):

1. **Restricted to 1990–2023 (34 obs, matching the literal thesis text, dropping 2024).**
   Re-estimate on the step-i-prepared 34-observation subset. If Model B (ARDL) is primary, note
   that lag selection may need to be re-run on the shorter sample (an even-shorter series can
   shift the AIC-optimal lag) — re-run lag selection rather than forcing the 35-obs-selected lag
   onto 34 observations, and note if the optimal lag changes.

2. **Excluding shock-year observations** (`SHOCK == 1`: 2008, 2009, 2020, 2021, 2022 dropped,
   leaving 30 observations). Re-estimate the primary model on this subset. Note: with the SHOCK
   dummy itself now degenerate (all remaining observations have SHOCK=0), drop the SHOCK
   regressor from this specific re-estimation rather than including a constant zero column —
   state this adjustment explicitly.

3. **Using raw FDI instead of log(FDI).** Re-estimate the primary model with `fdi_net_inflows_usd`
   in place of `log_fdi`, full 1990–2024 sample, all else unchanged. This is the direct
   counter-check on the step-i log-transform deviation.

4. **Alternate ARDL lag length** (only applicable if Model B/ARDL is the primary model). If
   step vi's AIC-selected lag differed from the BIC-implied lag, re-estimate at the BIC-implied
   `(p,q)` as the alternate. If AIC and BIC agreed in step vi, instead re-estimate at one lag
   step away from the selected optimum (e.g., if optimal was (1,1), try (2,1) or (1,2), whichever
   is next-best by AIC) to show sensitivity. State which alternate lag was used and why.
   *(If Model A/OLS is primary — Branch A from step v — this check does not apply; note it as
   not applicable rather than silently skipping without comment.)*

## Formulas

- Same model equations as step vi (Model A or Model B, whichever is primary) — no new formulas,
  only changed sample/variable/lag inputs per check above.

## Decisions & flags

- Checks are run one-at-a-time by default, not stacked, so each check isolates one source of
  sensitivity — a combined "all four at once" version is optional and must be clearly labeled
  as a fifth, non-standard check if included.
- Dropping the SHOCK regressor in check 2 (rather than keeping a now-degenerate dummy) is a
  necessary adjustment, flagged explicitly rather than silently handled.
- Re-running ARDL lag selection on the 34-obs subset (check 1) rather than reusing the 35-obs
  lag — flagged as the chosen default; note if this changes the selected `(p,q)`.
- Check 4 is conditional on Model B being primary — explicitly marked not-applicable, not
  silently omitted, if Model A is primary.

## Outputs

- One results row per check (5 rows: baseline for reference + checks 1–4, or fewer if check 4 is
  not applicable), each showing: DIVP coefficient (and long-run DIVP coefficient, if ARDL), DIVM
  coefficient (and long-run, if ARDL), their p-values, and N.
- A short written assessment: do the DIVP/DIVM coefficients stay similar in sign, magnitude, and
  significance across all checks (→ supports confidence in H1/H2), or do they move materially
  under any specific check (→ flag which check and discuss why, e.g., "the 2022 crisis year is
  doing a lot of work" if excluding shock years flips a coefficient).

## Definition of done

- All four checks run against the primary model (check 4 explicitly marked N/A if not
  applicable).
- A single comparison table assembled: baseline vs. each of the four checks, DIVP/DIVM
  coefficients and significance side by side.
- Written interpretation of coefficient stability across checks, directly usable in Chapter 4
  draft section 7 and feeding back into section 5's H1/H2 confidence statement.
