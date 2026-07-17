# Plan d.ii — Descriptive Statistics and Trend Analysis

**Parent requirement:** [research_plan.md § d.ii](../../1_requirements/research_plan.md)
**Depends on:** [i — Data preparation](i_data_preparation.md) (uses the assembled 1990–2024
analysis frame)
**Feeds into:** Chapter 4 draft section 1 (addresses RQ1 directly); [iii — Stationarity
testing](iii_stationarity_testing.md) reads the same frame next

## Objective

Characterise each series numerically and visually before any modeling, and answer RQ1 directly
in plain language: *"How have PDI and MDI trended in Sri Lanka, 1990–2024?"*

## Inputs

- The 1990–2024 analysis frame from step i: `eri, divp, divm, inflation_rate_pct,
  exchange_rate, fdi_net_inflows_usd, log_fdi, shock`.

## Method / Steps

1. **Summary statistics table.** For each of `ERI, DIVP, DIVM, INF, EXR, FDI (raw), log(FDI)`
   report: N, mean, standard deviation, min, max (and optionally median, skewness, kurtosis —
   skewness/kurtosis are useful context for the Jarque-Bera test in step vii, so worth including
   here for continuity). Present as a single table, one row per variable.

2. **Time-series plots — ERI, PDI, MDI, 1990–2024.**
   - One combined line chart with all three series (note the scale difference: ERI, PDI, MDI are
     each bounded roughly 0–1, so they're visually comparable on one axis — confirm this before
     combining; if ERI's range differs meaningfully, consider a secondary axis).
   - Shade the shock periods. The SHOCK dummy flags 5 individual years
     (2008, 2009, 2020, 2021, 2022), which map to **three shock episodes**: the 2008–2009 Global
     Financial Crisis, the 2020–2021 COVID-19 shock, and the 2022 economic/debt crisis. Shade
     three separate bands rather than five individual year-slivers, and label each band.

3. **Supporting single-series plots.** Individual PDI and MDI trend lines (cleaner for spotting
   structural breaks than the combined chart), each with the same three shaded shock bands.

4. **Descriptive trend narrative (plain language, directly answers RQ1).** Using the plots and
   summary stats, describe:
   - Whether MDI is consistently higher than PDI across the sample (visual + mean comparison).
   - The overall direction of each series 1990→2024 (rising, falling, flat, or regime-shifting).
   - Whether either series shows a visible structural break/discontinuity around 2022 (the debt
     crisis / IMF program period) — note it, but do not test for a formal break statistically
     here (that's outside the scope of d.ii; flag as a candidate follow-up if a break looks
     visually strong).
   - How ERI moves relative to PDI/MDI over the same period, as scene-setting for the RQ2
     regression to come.

5. **Correlation snapshot (optional, light-touch).** A simple pairwise correlation matrix among
   ERI, DIVP, DIVM is a natural companion to the trend narrative here — but the *regressor*
   correlation matrix required for VIF cross-checking belongs in step iv, not here. Keep this
   step's scope to description/trend, not diagnostics.

## Formulas

- Standard descriptive statistics (mean, sample SD with `n−1` denominator, min, max); skewness
  and excess kurtosis using the standard moment-based formulas (or `scipy.stats.skew` /
  `scipy.stats.kurtosis` conventions — note which convention is used, since EViews' default
  differs slightly and this should be reproducible against it).

## Decisions & flags

- Three shaded shock episodes (2008–09, 2020–21, 2022) rather than five isolated year markers —
  this is an interpretive grouping of the SHOCK dummy for visualization only; the dummy itself
  stays as 5 individual years in the regression (step vi). State this explicitly so it isn't
  mistaken for a redefinition of SHOCK.
- Whether a visual structural break is called out around 2022 is a judgment call based on what
  the plot shows — describe what is seen, flag it as visual/descriptive only, not a formal test
  result.

## Outputs

- Descriptive statistics table (CSV + printed table).
- Combined ERI/PDI/MDI trend chart with shaded shock bands (PNG).
- Individual PDI and MDI trend charts (PNG).
- A short written trend narrative (a few paragraphs) answering RQ1, for direct inclusion in the
  Chapter 4 draft.

## Definition of done

- Summary stats computed for all 7 series (5 core + FDI raw/log).
- All three trend charts produced with correctly shaded shock episodes.
- RQ1 answered in plain language, grounded in the specific numbers/plots produced (not generic
  statements).
