# Plan d.viii — Robustness Checks

**Parent requirement:** [research_plan.md § d.viii](../../1_requirements/research_plan.md)
**Depends on:** [vi — Estimation](vi_estimation.md) (re-estimates the primary model under
alternate conditions), [vii — Post-estimation diagnostics](vii_post_estimation_diagnostics.md)
(redesignated the primary model — see Update below), [i — Data preparation](i_data_preparation.md)
(uses the 1990–2023 subset and raw-FDI columns already prepared there)
**Feeds into:** Chapter 4 draft section 7 (robustness summary); directly supports or undermines
confidence in H1/H2 alongside section 5's interpretation

> **Update, 2026-07-17 — primary model redesignated before this step was implemented.** This
> plan originally read "primary model = Model B/ARDL if Branch B was selected." Branch B *was*
> selected, but step vi's ARDL bounds test did not confirm cointegration at either the
> grid-searched AIC(1,2) or leanest capped ARDL(1,1) specification, and step vii's
> Breusch-Godfrey test flagged uncorrected serial correlation in the capped ARDL(1,1) at lag 2
> (significant at 5%). **The first-differenced OLS is now the primary model for H1/H2
> inference; ARDL(1,1) is secondary/exploratory.** Same correction already applied to
> `research_plan.md` (§a Update note, §e Model B heading) and `outputs/modeling_path_decision.csv`
> (addendum). Every "primary model" reference below means the first-differenced OLS unless
> stated otherwise.

## Objective

Re-estimate the **first-differenced OLS (primary model, redesignated 2026-07-17)** under four
alternate conditions, and report how much the DIVP/DIVM coefficients move — this is the
evidentiary basis for how much confidence to place in H1/H2. ARDL(1,1) is not the primary model,
but check 4 (lag-length sensitivity) remains relevant to it as a secondary/exploratory check,
since ARDL(1,1) is still reported alongside in the Chapter 4 write-up.

## Inputs

- The first-differenced OLS specification and fitted result from step vi (redesignated primary
  as of step vii; see Update above). The capped ARDL(1,1) result from step vi/vii is also
  available for the secondary/exploratory lag-sensitivity check (check 4).
- The 1990–2023 subset (34 obs) prepared in step i.
- Both the log(FDI) and raw-FDI columns from step i.

## Method / Steps

Re-estimate the **first-differenced OLS (primary model)** under each of the following four
conditions, one at a time (i.e., changing one thing per check, not stacking all four together
initially — a stacked "kitchen sink" version can optionally be added at the end as a fifth,
clearly-labeled check):

1. **Restricted to 1990–2023 (34 obs pre-differencing → 33 post-differencing, matching the
   literal thesis text, dropping 2024).** Re-estimate the first-differenced OLS on the
   step-i-prepared 34-observation subset (differenced down to 33). No lag-selection re-run
   needed — the first-differenced OLS has no lag structure to reselect, unlike ARDL. *(If ARDL(1,1)
   is also re-estimated on this subset as secondary/exploratory context, note that its lag
   selection may need to be re-run on the shorter sample per the original guidance — optional,
   not required for the primary-model robustness story.)*

2. **Excluding shock-year observations** (`SHOCK == 1`: 2008, 2009, 2020, 2021, 2022 dropped,
   leaving 30 observations, 29 post-differencing). Re-estimate the first-differenced OLS on this
   subset. Note: with the SHOCK dummy itself now degenerate (all remaining observations have
   SHOCK=0), drop the SHOCK regressor from this specific re-estimation rather than including a
   constant zero column — state this adjustment explicitly.

3. **Using raw FDI instead of log(FDI).** Re-estimate the first-differenced OLS with
   `Δfdi_net_inflows_usd` in place of `Δlog_fdi`, full 1990–2024 sample, all else unchanged. This
   is the direct counter-check on the step-i log-transform deviation.

4. **Alternate ARDL lag length — secondary/exploratory only, not a primary-model check.** The
   first-differenced OLS has no lag structure, so this check does not apply to the primary model
   as originally scoped; **mark it N/A for the primary-model comparison table**, not silently
   omitted. Because ARDL(1,1) is still reported alongside as secondary/exploratory context, its
   lag-length sensitivity remains informative and was already substantially explored in step vi
   (grid-search AIC(1,2) vs. BIC-implied (2,1)) and step vii (leanest capped ARDL(1,1) vs. the
   grid-search pick, run specifically as a degrees-of-freedom robustness check) — both reached
   the same substantive conclusion (bounds test inconclusive). Re-running it a third time here is
   optional; if run, report it as a clearly-labeled secondary-model check, separate from the
   primary-model comparison table.

## Formulas

- Same model equation as step vi's first-differenced OLS (the primary model) — no new formulas,
  only changed sample/variable inputs per checks 1–3 above. Check 4 (if run) uses ARDL(1,1)'s
  equation as secondary/exploratory context, not the primary-model equation.

## Decisions & flags

- Checks are run one-at-a-time by default, not stacked, so each check isolates one source of
  sensitivity — a combined "all four at once" version is optional and must be clearly labeled
  as a fifth, non-standard check if included.
- Dropping the SHOCK regressor in check 2 (rather than keeping a now-degenerate dummy) is a
  necessary adjustment, flagged explicitly rather than silently handled.
- **Check 4 is N/A for the primary-model comparison table** (the first-differenced OLS has no
  lag structure) — explicitly marked not-applicable, not silently omitted, same as the original
  Model-A-primary case this plan already anticipated. Optionally reported as a separate,
  clearly-labeled secondary/exploratory check on ARDL(1,1) instead.
- Given the Newey-West HAC-robust check already run on the first-differenced OLS in step vii
  (`outputs/model_diff_hac_coefficients.csv` — see that notebook's Step 6c) because its
  Durbin-Watson result was inconclusive rather than clean, this step's baseline row should cite
  **both** the original and HAC-robust DIVP/DIVM p-values for the unmodified 1990–2024
  specification, not just the original SEs, so the robustness table is read against the same
  standard already applied upstream.

## Outputs

- One results row per check (5 rows: baseline for reference + checks 1–3 + check 4 marked N/A,
  or a secondary ARDL(1,1) table if check 4 is run as exploratory context), each showing: DIVP
  coefficient, DIVM coefficient, their original and HAC-robust p-values, and N.
- A short written assessment: do the DIVP/DIVM coefficients stay similar in sign, magnitude, and
  significance across all checks (→ supports confidence in H1/H2), or do they move materially
  under any specific check (→ flag which check and discuss why, e.g., "the 2022 crisis year is
  doing a lot of work" if excluding shock years flips a coefficient). Given DIVP's baseline
  result is only marginal (10% level, and sensitive to the HAC correction — see step vii), pay
  particular attention to whether any check pushes it across the 5%/10% boundary in either
  direction.

## Definition of done

- Checks 1–3 run against the first-differenced OLS (primary model); check 4 explicitly marked
  N/A for the primary-model table (optionally run separately as ARDL(1,1) secondary context).
- A single comparison table assembled: baseline (with original and HAC p-values) vs. each of
  checks 1–3, DIVP/DIVM coefficients and significance side by side.
- Written interpretation of coefficient stability across checks, directly usable in Chapter 4
  draft section 7 and feeding back into section 5's H1/H2 confidence statement — explicitly
  addressing whether DIVP's marginal (10%-level) baseline result holds up.
