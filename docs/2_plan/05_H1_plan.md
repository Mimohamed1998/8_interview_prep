# H1 Analysis Plan

**H1: AI preparedness has a positive impact on sustainability performance.**

**Data required:** `data/3_processed_data/master_features/panel_dataset_2020_2023.parquet`
- Key variables: `ai_readiness_score` (IV), `sdg_index_score` (DV), `year`, `country`, `country_group`, `iso_code`

> **Basis for `country_group`:** The `country_group` column is a study-defined purposive sampling variable that stratifies the 15 selected countries into three tiers based on their combined income level and governance profile: (1) *Developed* — World Bank High Income economies (World Bank, 2023) with WGI composite scores above the global 75th percentile; (2) *Developing* — World Bank Upper-Middle Income economies with moderate WGI profiles; (3) *Lower Governance* — Lower-Middle Income economies with WGI composite scores below the global median. The robustness check in Step 3 uses this stratification to verify whether the AI Readiness → SDG relationship holds consistently across all three tiers. Classification sources: World Bank Country Classification System (World Bank, 2023, https://datahelpdesk.worldbank.org/knowledgebase/articles/906519); WGI percentile thresholds from Kaufmann, D., Kraay, A., & Mastruzzi, M. (2010). World Bank Policy Research Working Paper No. 5430.

H1 is tested using the results from the RQ1 analysis. This plan describes the specific hypothesis testing steps and reporting requirements on top of the RQ1 regression models.

---

## Hypothesis Formulation

- **Null Hypothesis (H0):** β1 ≤ 0 — AI readiness has no positive impact on sustainability (coefficient is zero or negative)
- **Alternative Hypothesis (H1):** β1 > 0 — AI readiness has a statistically significant positive impact on sustainability

This is a **one-tailed** test (directional hypothesis).

---

## Step 1 — Extract β1 from RQ1 Panel Regression

From the selected panel model (Fixed Effects or Random Effects, per Hausman test in RQ1):

- Report coefficient β1 for `ai_readiness_score`
- Report standard error (SE)
- Compute one-tailed t-statistic: `t = β1 / SE`
- Compute one-tailed p-value: `p = P(T > t)` with df = (n − k − 1)
- Report 95% one-tailed confidence interval lower bound: `β1 − 1.645 × SE`

**Decision rule:**
- If β1 > 0 AND p < 0.05 (one-tailed) → Reject H0, support H1
- If β1 ≤ 0 OR p ≥ 0.05 → Fail to reject H0, H1 not supported

---

## Step 2 — Effect Size Reporting

Compute and report:
- **Cohen's f² (for regression effect size):**
  `f² = R²_full / (1 − R²_full)`
  - f² ≥ 0.02: small effect
  - f² ≥ 0.15: medium effect
  - f² ≥ 0.35: large effect

- **Standardized beta coefficient:** Re-run regression with z-scored variables to obtain the standardized β1 (scale-independent effect size)

---

## Step 3 — Robustness Checks for H1

To ensure the finding for H1 is not driven by model choice or outliers:

1. **Outlier check:** Identify influential observations using Cook's Distance; re-run regression excluding outliers; check if sign and significance of β1 remain unchanged
2. **Year-by-year check:** Run the regression separately for each year (2020, 2021, 2022, 2023) and confirm that β1 is consistently positive across all years
3. **Country-group check:** Run the regression separately for Developed, Developing, and Lower Governance groups; check if β1 is positive in all three subsets
4. **Lagged predictor check (optional):** If data permits, test whether AI Readiness in year t predicts SDG score in year t+1 (one-year lag); this strengthens the causal narrative

---

## Step 4 — Visualization for H1

1. **Annotated scatter plot:** AI Readiness (x) vs SDG Score (y), with a fitted regression line and the equation displayed (slope = β1, R² shown)
2. **Coefficient plot:** Point estimate for β1 with 95% confidence interval; the interval should not cross zero for H1 to be supported
3. **Year-panel plot:** Four scatter sub-plots (one per year 2020–2023) showing the AI-SDG relationship in each cross-section

---

## Step 5 — Reporting H1 Results

Produce a concise results table:

| Model | β1 (AI Readiness) | SE | t-stat | p-value (1-tail) | 95% CI | Decision |
|-------|-------------------|----|--------|-----------------|--------|----------|
| Pooled OLS | | | | | | |
| Fixed Effects | | | | | | |
| Random Effects | | | | | | |
| Selected model | | | | | | |

**Narrative conclusion example:**
> "The Fixed Effects panel regression revealed a statistically significant positive association between AI Readiness and SDG Index scores (β1 = [X], SE = [X], t = [X], p = [X], one-tailed). This supports H1: countries with higher AI preparedness tend to achieve better sustainability outcomes. The effect size (Cohen's f² = [X]) indicates a [small/medium/large] practical effect."

---

## Expected Output Files

| File | Content |
|------|---------|
| `outputs/h1_hypothesis_test_table.csv` | Coefficient table across models |
| `outputs/h1_coefficient_plot.png` | β1 with confidence interval |
| `outputs/h1_robustness_checks.csv` | Year-by-year and group-level β1 values |
| `outputs/h1_scatter_annotated.png` | Regression scatter with equation |
