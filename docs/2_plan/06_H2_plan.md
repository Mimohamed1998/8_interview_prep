# H2 Analysis Plan

**H2: Quality of governance has a positive relationship with sustainability.**

**Data required:** `data/3_processed_data/master_features/panel_dataset_2020_2023.parquet`
- Key variables: `wgi_composite` (IV), `sdg_index_score` (DV), `year`, `country`, `country_group`, `iso_code`

> **Basis for `country_group`:** The `country_group` column is a study-defined purposive sampling variable that stratifies the 15 selected countries into three tiers based on their combined income level and governance profile: (1) *Developed* — World Bank High Income economies (World Bank, 2023) with WGI composite scores above the global 75th percentile; (2) *Developing* — World Bank Upper-Middle Income economies with moderate WGI profiles; (3) *Lower Governance* — Lower-Middle Income economies with WGI composite scores below the global median. Classification sources: World Bank Country Classification System (World Bank, 2023, https://datahelpdesk.worldbank.org/knowledgebase/articles/906519); WGI percentile thresholds from Kaufmann, D., Kraay, A., & Mastruzzi, M. (2010). World Bank Policy Research Working Paper No. 5430.

H2 is tested using the results from the RQ2 analysis. This plan specifies the hypothesis testing and reporting steps on top of the RQ2 regression models.

---

## Hypothesis Formulation

- **Null Hypothesis (H0):** β1 ≤ 0 — Governance quality has no positive relationship with sustainability
- **Alternative Hypothesis (H2):** β1 > 0 — Governance quality has a statistically significant positive relationship with sustainability

This is a **one-tailed** test (directional hypothesis).

---

## Step 1 — Extract β1 from RQ2 Panel Regression

From the selected panel model (Fixed Effects or Random Effects, per Hausman test in RQ2):

- Report coefficient β1 for `wgi_composite`
- Report standard error (SE)
- Compute one-tailed t-statistic: `t = β1 / SE`
- Compute one-tailed p-value: `p = P(T > t)`
- Report 95% one-tailed confidence interval lower bound: `β1 − 1.645 × SE`

**Decision rule:**
- If β1 > 0 AND p < 0.05 (one-tailed) → Reject H0, support H2
- If β1 ≤ 0 OR p ≥ 0.05 → Fail to reject H0, H2 not supported

---

## Step 2 — Effect Size Reporting

- **Cohen's f²:** `f² = R²_full / (1 − R²_full)` for the RQ2 model
- **Standardized beta coefficient:** z-score both variables and re-run regression to get scale-free β1
- **Pearson r:** Report the bivariate correlation between `wgi_composite` and `sdg_index_score` as an intuitive effect size

---

## Step 3 — Additional Evidence: Between-Group Analysis

To further substantiate H2 with group-level evidence using the study's purposive sampling stratification.

**Group classification basis:** Countries are grouped using the `country_group` variable in the panel dataset, which classifies all 15 countries into three governance-income tiers (see data provenance note above). The three tiers — *Developed*, *Developing*, and *Lower Governance* — represent a decreasing gradient of both WGI composite score and income level, enabling a directional test of H2 at the group level.

> **Literature basis for between-group comparison:** Between-group mean comparison stratified by governance tier is a standard supplementary test in governance-development studies. This approach is consistent with the UNDP Human Development Report's (UNDP, 2023) practice of comparing outcome means across HDI quartile tiers, and with Kaufmann & Kraay's (2002, *Economia*, 3(1), 169–229) framework for assessing governance–growth gradients across country clusters.

1. **Group mean comparison:**
   - Using the `country_group` variable, compute mean `sdg_index_score` for each of the three tiers:
     - *Developed* group (highest WGI tier)
     - *Developing* group (middle WGI tier)
     - *Lower Governance* group (lowest WGI tier)
   - Expectation: mean SDG score decreases monotonically as governance tier decreases — consistent with H2

2. **One-way ANOVA / Kruskal-Wallis test:**
   - Test whether mean SDG scores differ significantly across the three governance tiers
   - Use ANOVA if SDG scores within groups are approximately normally distributed; use Kruskal-Wallis (non-parametric) if normality is violated (Shapiro-Wilk test, p < 0.05)
   - Report: F-statistic (or H-statistic), degrees of freedom, p-value
   - If significant (p < 0.05): run post-hoc pairwise comparisons — Tukey HSD (for ANOVA) or Mann-Whitney U with Bonferroni correction (for Kruskal-Wallis)

3. **Spearman rank correlation:**
   - Rank all 15 countries by their average `wgi_composite` (2020–2023) and by their average `sdg_index_score` (2020–2023)
   - Compute Spearman's ρ (rho) between the two country-level rankings
   - Report: ρ value, p-value, 95% confidence interval
   - A positive, statistically significant ρ supports H2 at the country level (higher governance rank → higher SDG rank)
   - Note: Spearman's ρ is preferred over Pearson r here because it is robust to non-linearity and the small N=15 country-level ranking

---

## Step 4 — Robustness Checks for H2

1. **Outlier check:** Identify and flag influential country-years using Cook's Distance; re-run model without them; confirm β1 remains positive and significant
2. **Year-by-year cross-sections:** Run OLS for each year separately (2020, 2021, 2022, 2023); check if governance coefficient is consistently positive
3. **Individual WGI dimensions:** Run the regression 6 times, once per individual WGI dimension (VA, PV, GE, RQ, RL, CC), to identify which governance dimension drives the relationship most strongly
4. **Alternative moderator scaling:** Test both raw WGI scale (−2.5 to +2.5) and percentile rank (0–100) to verify the finding is not scale-dependent

---

## Step 5 — Visualization for H2

1. **Scatter plot:** WGI composite (x) vs SDG Index score (y)
   - Color-code by country group
   - Add OLS regression line with 95% confidence band
   - Label each country point

2. **Bar chart with error bars:** Average SDG score by country group, with standard error bars (clearly shows the group-level gradient)

3. **Coefficient plot:** β1 (WGI) from multiple models (pooled OLS, FE, RE, each year) plotted as point estimates with 95% CIs

4. **Heatmap:** 15 countries × 4 years showing WGI composite value (color intensity), side by side with a similar heatmap for SDG score — visual alignment supports H2

---

## Step 6 — Reporting H2 Results

Produce a concise results table:

| Model | β1 (WGI Composite) | SE | t-stat | p-value (1-tail) | 95% CI | Decision |
|-------|--------------------|----|--------|-----------------|--------|----------|
| Pooled OLS | | | | | | |
| Fixed Effects | | | | | | |
| Random Effects | | | | | | |
| Selected model | | | | | | |

**Narrative conclusion example:**
> "The panel regression results indicate a statistically significant positive relationship between governance quality (WGI composite) and sustainability outcomes (SDG Index score) (β1 = [X], SE = [X], t = [X], p = [X], one-tailed). This supports H2. The between-group analysis further confirms this gradient: the Developed tier (highest WGI) achieved a mean SDG score of [X], compared to [X] in the Developing tier and [X] in the Lower Governance tier (ANOVA/Kruskal-Wallis: F/H = [X], p = [X]). Country-level Spearman rank correlation between WGI and SDG scores was ρ = [X] (p = [X]), consistent with H2."

---

## Expected Output Files

| File | Content |
|------|---------|
| `outputs/h2_hypothesis_test_table.csv` | Coefficient table across models |
| `outputs/h2_scatter_plot.png` | WGI vs SDG scatter with regression line |
| `outputs/h2_group_bar_chart.png` | Mean SDG by governance group |
| `outputs/h2_coefficient_plot.png` | β1 across models with CIs |
| `outputs/h2_dimension_analysis.csv` | Individual WGI dimension regressions |
| `outputs/h2_robustness_checks.csv` | Year-by-year coefficients |
