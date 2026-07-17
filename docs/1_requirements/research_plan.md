# Project Requirements: Export Diversification and Economic Resilience (Sri Lanka, 1990–2024)

## 4. Project Requirements

### a. What is this project about?

This is the empirical chapter of a quantitative thesis, *"Evaluating the Relationship Between
Export Diversification and Economic Resilience: Evidence from Sri Lanka."* The thesis argues
that Sri Lanka's export base has remained concentrated in a small number of products (apparel,
tea, rubber, coconut) and destination markets (USA, EU) since the 1977 liberalisation reforms,
and tests whether **broadening that base (diversification) is associated with greater
macroeconomic resilience**, using annual data from 1990 to 2024 (35 observations — extended
one year beyond the 1990–2023 scope stated in the attached thesis PDF; see data note below).

**Modeling approach — hybrid, decided by the data, not fixed in advance.** The thesis's
written methodology (Ch. 3.5) specifies a static OLS model. That is only valid if all
regressors are stationary. Given the visible trends in the exchange rate and FDI series, this
project runs **OLS as the literal-thesis baseline**, but if stationarity testing (step d.iii)
shows a mix of I(0)/I(1) variables, **ARDL bounds testing (Pesaran, Shin & Smith, 2001) was
planned to become the primary model for inference** ⚠️ **[Superseded 2026-07-17 — see Update
below]**, with OLS retained and reported alongside it as the methodology-baseline comparison.
Rationale: with 6 regressors and ~34–35 annual observations, OLS-on-levels with a trending
regressor risks a spurious regression, OLS-on-differences loses the long-run relationship the
research questions actually ask about, and a full Johansen VECM is over-parameterised for this
sample size — ARDL is the standard, sample-efficient response to exactly this situation (mixed
integration orders, small T, a genuine long-run question). See Section e for both
specifications.

> **Update, 2026-07-17 — primary model redesignated after post-estimation diagnostics (step
> vii).** Branch B was confirmed (mixed I(0)/I(1), no I(2)), so ARDL was estimated as planned.
> But the ARDL bounds test (step vi) did not confirm cointegration at either the grid-searched
> AIC(1,2) specification (F=2.8230 vs. 5% bounds [2.328, 3.500]) or the leanest capped ARDL(1,1)
> specification (F=2.3658, same bounds) — both inconclusive at 5%, both below the 1% lower
> bound. Step vii's Breusch-Godfrey test additionally flagged uncorrected serial correlation in
> the capped ARDL(1,1) at lag 2 (LM(2)=6.841, p=0.0327, significant at 5%; the lag-1 result
> matching the model's own lag structure was only borderline, p=0.0685). The first-differenced
> OLS, by contrast, passed its full step vii diagnostic battery cleanly. **Decision: the
> first-differenced OLS is now the primary model for H1/H2 inference; ARDL(1,1) is retained and
> reported as a secondary/exploratory specification**, not the primary evidentiary basis for
> H1/H2. Static OLS on levels remains the literal-thesis baseline, unchanged. Full rationale and
> evidence trail: `outputs/modeling_path_decision.csv` (addendum), `outputs/diagnostics_model_b_ardl_capped.csv`,
> `outputs/diagnostics_model_diff_ols.csv`.

The theoretical grounding is: classical trade theory (specialisation vs. vulnerability),
portfolio diversification theory (Markowitz, applied to export revenue volatility), and
Briguglio et al.'s (2009) economic resilience framework (absorptive, adaptive, restorative
capacity). Full literature review and theoretical framework are in the attached thesis PDF
(Chapters 1–2) — read these first for context before writing any code.

### b. What are the data sources?

All four CSVs are in this project's data folder:

| File | Contents | Role |
|---|---|---|
| `Main_Data_Sheet.csv` | Year, ERI, PDI, MDI, Inflation Rate, FDI (current USD), Exchange Rate (LKR/USD), 1990–2024 | **Primary regression-ready panel** |
| `Economic_Recillience_Index.csv` | Year, GDP Growth %, Unemployment %, TB Ratio (% GDP), normalized components (N_GDP, N_Unemp inv, N_TB inv), ERI | ERI construction detail — use to **verify** the ERI column in the main sheet, not to rebuild it |
| `Product_Diversification_Index.csv` | Export values (USD mn) by 17 product categories, 1986–2024 | Raw data behind PDI — use to **verify** PDI via HHI recomputation |
| `Market_Diversification_Index.csv` | Export values (USD) by 21 destination countries + "Others"/Total, 1990–2024 | Raw data behind MDI — use to **verify** MDI via HHI recomputation |

Underlying sources per the thesis (Ch. 3.2): Central Bank of Sri Lanka (CBSL) Annual Reports
and Statistical Appendix, Export Development Board (EDB), IMF Direction of Trade Statistics
(1995–98 gap-fill), World Bank World Development Indicators (GDP in current USD).

**Study period — extended from the written thesis scope.** `Main_Data_Sheet.csv` has 35 rows
(1990–2024). Chapter 3.2/3.8 of the attached PDF states the scope as 1990–2023 (34
observations); **use the full 1990–2024 (35 observations) as the primary dataset instead** —
this is a deliberate extension beyond what's written in the methodology chapter, so note it
explicitly wherever the study period is stated (e.g., "this analysis extends the stated
1990–2023 period by one year to incorporate the most recent available data"), rather than
silently treating 35 as 34. Run 1990–2023 (34 obs, matching the literal thesis text) as a
robustness/comparison check to show whether adding 2024 changes the conclusions.

### c. What are you trying to solve?

Two research questions from Ch. 1.5:
1. How have export product diversification (PDI) and market diversification (MDI) trended
   in Sri Lanka between 1990 and 2024?
2. What is the effect of PDI and MDI on economic resilience (ERI), controlling for inflation,
   exchange rate, FDI, and major shock episodes — both in the short run and, if a long-run
   (cointegrating) relationship exists, in the long run?

Hypotheses to test (from Ch. 3.5):
- **H1:** β₁ (DIVP/PDI) is positive and statistically significant → higher product
  diversification is associated with higher resilience.
- **H2:** β₂ (DIVM/MDI) is positive and statistically significant → higher market
  diversification is associated with higher resilience.
- If either coefficient is negative and significant, that is a real finding — do not treat it
  as an error. Report it and flag it for discussion against the literature in Ch. 2 (there is
  an active debate there on product vs. market diversification effectiveness).
- If ARDL bounds testing is triggered (see Section e), test H1/H2 on the **long-run**
  coefficients primarily, and report the short-run (error-correction) coefficients as
  supplementary evidence on adjustment speed.

### d. Analysis to be conducted

i. **Data preparation.** Merge the four CSVs on year. Construct the `SHOCK` dummy variable
   (=1 for 2008, 2009, 2020, 2021, 2022; =0 otherwise — per Ch. 3.3.3(d)). Recompute PDI and
   MDI independently from the raw product/market CSVs using the HHI formula (`DIVP = 1 − Σsᵢ²`)
   and cross-check against the pre-computed PDI/MDI columns in `Main_Data_Sheet.csv` — report
   any discrepancy rather than silently using one or the other. Use the full 1990–2024 range
   (35 obs) as the baseline dataset (see study period note above). Log-transform FDI
   (`log(FDI)`) given its scale runs from ~$43M to ~$1.6B against 0–1 bounded indices — this
   is a deviation from the literal thesis spec, so state it explicitly as an added
   transformation with justification, and also report the model using raw FDI as a robustness
   check.

ii. **Descriptive statistics and trend analysis.** Summary stats (mean, SD, min, max) for all
    variables. Time-series plots of ERI, PDI, and MDI 1990–2024, with the three shock periods
    shaded. This addresses RQ1 directly — describe the trend in plain language (e.g., is MDI
    consistently higher than PDI? Does either show a structural break around 2022?).

iii. **Stationarity testing (ADF, Augmented Dickey-Fuller).** Run on all six variables (ERI,
    PDI, MDI, INF, log(FDI), EXR) before any regression. Report the test statistic, p-value,
    and conclusion — stationary at level, I(0), or non-stationary at level (test the first
    difference too, to confirm I(1) and rule out I(2), since ARDL bounds testing is invalid if
    any variable is I(2)). **This result determines the modeling path — see the decision
    branch below and Section e.**

iv. **Multicollinearity check (VIF).** Compute Variance Inflation Factors for the regressor
    set. Flag any VIF > 10. Also report a plain correlation matrix for the regressors as an
    easy EViews cross-check.

v. **Decision branch (read before estimating anything).**
    - **If ADF shows all six variables are I(0)** (stationary at level): proceed with static
      OLS on levels as specified in the thesis (Ch. 3.5, Eq. 3.1). This is the simplest
      correct model — no need for ARDL.
    - **If ADF shows a mix of I(0) and I(1) variables, with none I(2):** this is the expected
      result given EXR's and likely FDI's visible trends. Running static OLS on levels here
      risks a spurious regression (significant coefficients driven by shared trends, not a
      real relationship). **Estimate an ARDL(p,q) bounds-testing model as the primary model**
      (see Section e). Still estimate the literal-thesis static OLS on levels too, and OLS on
      first-differenced variables, and present all three side by side — this shows the reader
      exactly what changes and why the ARDL result is preferred.
    - **If any variable is I(2):** flag this immediately and do not proceed with ARDL (bounds
      testing is invalid with I(2) regressors) — stop and report this back before continuing,
      since it would require a different approach (e.g., further differencing or dropping/
      transforming that variable).

vi. **Estimation**, per the branch selected in step v. See Section e for both model
    specifications.

vii. **Post-estimation diagnostics**, in this order, applied to whichever model(s) were
    estimated in step vi:
    - Durbin-Watson statistic (autocorrelation) — for OLS. For ARDL, use the Breusch-Godfrey
      LM test instead (DW is unreliable with lagged dependent variables, which ARDL includes).
    - Breusch-Pagan test (heteroskedasticity).
    - Jarque-Bera test (residual normality) — not in the thesis methodology chapter but
      standard practice; include it since it's a one-line addition and easy to reproduce in
      EViews.
    - Ramsey RESET test (functional form misspecification) — same reasoning as above.
    - For ARDL specifically: report the bounds test F-statistic against Pesaran et al. (2001)
      critical value bounds to confirm cointegration before interpreting long-run
      coefficients, plus the CUSUM/CUSUMSQ stability check if feasible.
    - If heteroskedasticity or autocorrelation is detected in the OLS model, re-estimate with
      Newey-West HAC standard errors and report **both** the original and robust standard
      errors side by side so they can be compared against EViews output.

viii. **Robustness checks.** Re-estimate the primary model: (1) restricted to 1990–2023
    (matching the literal thesis text, dropping 2024), (2) excluding shock-year observations,
    (3) using raw FDI instead of log(FDI), (4) with alternate ARDL lag length if AIC/BIC
    suggests a different optimal lag than the initial choice. Report how much the DIVP/DIVM
    coefficients move across these — this is what supports or undermines confidence in H1/H2.

### e. Modeling requirements

**Model A — Static OLS (literal thesis specification, Ch. 3.5, Eq. 3.1).** Always estimate
this, regardless of the ADF outcome, as the baseline for comparison against EViews and against
the written methodology chapter:

```
ERI = β0 + β1·DIVP + β2·DIVM + β3·INF + β4·EXR + β5·log(FDI) + β6·SHOCK + ε
```

**Model B — ARDL(p,q) bounds testing (secondary/exploratory as of 2026-07-17 — see the Update
note under "Modeling approach" above; originally planned as the primary model if step d.v
triggered Branch B, but the bounds test did not confirm cointegration and step vii flagged
uncorrected serial correlation, so the first-differenced OLS is now primary for H1/H2).**
Conditional Error Correction (ECM) form:

```
ΔERI_t = α0 + Σγᵢ·ΔERI_(t-i) + Σδⱼ·ΔX_(t-j) + θ1·ERI_(t-1) + θ2·DIVP_(t-1) + θ3·DIVM_(t-1)
         + θ4·INF_(t-1) + θ5·EXR_(t-1) + θ6·log(FDI)_(t-1) + θ7·SHOCK_(t-1) + ε_t
```
where X = {DIVP, DIVM, INF, EXR, log(FDI), SHOCK}. Steps:
1. Select optimal lag length p,q via AIC (and report BIC for comparison) — with only ~34–35
   observations, keep the maximum lag small (1–2) to preserve degrees of freedom.
2. Run the bounds F-test on the joint significance of the lagged levels (θ1…θ7) against
   Pesaran et al. (2001) critical value bounds. F-stat above the upper bound → cointegration
   confirmed → long-run relationship exists and long-run coefficients are interpretable.
   Below the lower bound → no cointegration → fall back to the differenced-OLS or ARDL
   short-run-only interpretation. Between the bounds → inconclusive, report as such.
3. If cointegration is confirmed, derive and report the **long-run coefficients**
   (long-run β = −θₖ/θ1 for each regressor) — these are what H1/H2 should be tested against.
   Report the **error-correction term** (should be negative and significant, ideally between
   −1 and 0) — its magnitude is the speed of adjustment back to the long-run resilience level
   after a shock, which is directly relevant to your resilience framework (Ch. 2.3,
   "restorative capacity").
4. Report short-run coefficients (the Δ terms) as supplementary evidence.

**For both models:**
- Estimation: Python `statsmodels` (`statsmodels.api.OLS` for Model A;
  `statsmodels.tsa.ardl.ARDL` or an equivalent bounds-testing implementation for Model B —
  note in the output which package/function was used, since EViews' built-in ARDL wizard will
  produce the estimates I'll compare against).
- Print full summary tables — coefficient, std error, t-stat, p-value, R², adjusted R², F-stat
  (plus the bounds-test F-stat and long-run coefficients for Model B) — since every number
  will be cross-checked in EViews.
- Significance thresholds: report at 1%, 5%, and 10% levels (***/**/* convention).
- Explain the reasoning behind every step in plain language as you go — not just the code and
  output, but *why* that test comes next and what a given result implies for the next
  decision. I'm cross-verifying every number in EViews, so I need to be able to follow and
  reproduce each step manually, not just trust a final table.
- If Model B is triggered, explicitly contrast Model A and Model B results in the write-up:
  what would a naive reader conclude from the (potentially spurious) static OLS, versus what
  the ARDL long-run relationship actually shows, and why the difference matters.

### f. Summarize the result

Deliverable is a draft of **Chapter 4: Empirical Analysis and Findings**, structured as:

1. Descriptive statistics table + trend charts (addresses RQ1).
2. Diagnostic test results table (ADF — levels and first differences, VIF, and whichever of
   DW/Breusch-Godfrey, Breusch-Pagan, Jarque-Bera, RESET, and the ARDL bounds test apply) with
   plain-language interpretation of each, in the sequence run.
3. Model A (static OLS) regression table — coefficients, SEs (original and robust if
   applicable), significance stars, R², adjusted R², F-stat, N.
4. If triggered, Model B (ARDL) results: lag selection rationale, bounds test outcome,
   long-run coefficient table, error-correction term, short-run coefficient table.
5. Interpretation tied explicitly back to H1 and H2 — using the long-run ARDL coefficients if
   Model B applies, otherwise the OLS coefficients — state whether each is supported,
   rejected, or ambiguous, and by how much (economic significance, not just statistical
   significance — e.g., "a 0.1 increase in PDI is associated with a Δ ERI of X in the long
   run, holding other variables constant").
6. A short discussion paragraph connecting the findings to the Ch. 2 literature (e.g., does
   this support the "product diversification matters more than market diversification" side of
   the debate, or the reverse? How does the 2022 crisis show up in the residuals, the SHOCK
   coefficient, or the speed of the error-correction term?).
7. Robustness check summary (from step viii) — do the core results hold up?

## Additional requirements

- **Audience and purpose:** I will personally re-run every regression and test in EViews to
  verify these results, so prioritize showing your work (test statistics, formulas used,
  intermediate values, lag-selection criteria) over polished narrative. Detailed reasoning at
  each step matters more than brevity here.
- **Flag deviations.** Anywhere the analysis deviates from the literal wording of the thesis
  methodology chapter (log-transforming FDI, extending to 2024, first-differencing a variable,
  adding Jarque-Bera/RESET tests not in Ch. 3.7, moving to ARDL as the primary model instead
  of static OLS), call it out explicitly with a one-line justification, rather than silently
  making the change.
- **Don't guess on judgment calls that change the model materially** (e.g., ARDL lag length
  choice if AIC and BIC disagree, what to do if a variable tests as I(2)) — flag the decision,
  state the default you're using, and note the alternative so I can override it. The study
  period is already settled: use 1990–2024 (35 obs) as the baseline, 1990–2023 as the
  robustness check. The modeling approach was originally settled as: OLS always reported as the
  literal-thesis baseline; ARDL primary for inference only if ADF confirms mixed I(0)/I(1)
  regressors with no I(2). **Superseded 2026-07-17** (see the Update note under "Modeling
  approach" in Section a): Branch B did trigger, but the ARDL bounds test came back
  inconclusive and step vii flagged uncorrected serial correlation in the ARDL residuals, so
  this was itself a judgment call flagged and made on the user's explicit direction, not
  guessed — the first-differenced OLS is now primary for H1/H2, ARDL(1,1) secondary/exploratory.
- **Output format:** save all code (Python scripts or notebook), the regression/diagnostic
  output, and charts to an outputs folder. Produce the Chapter 4 draft as a separate markdown
  or Word document, written in formal academic thesis style consistent with the tone of the
  attached PDF (Chapters 1–3).
- **Source material:** the full thesis PDF (Chapters 1–3, including the reference list) is
  attached for context — pull terminology, variable names, and citation style from it
  consistently rather than introducing new notation.