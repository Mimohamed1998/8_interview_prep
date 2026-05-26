# RQ1 Analysis Plan

**RQ1: Does AI preparedness have any influence on sustainability outcomes?**

**Data required:** `data/3_processed_data/master_features/panel_dataset_2020_2023.parquet`
- Key variables: `ai_readiness_score` (IV), `sdg_index_score` (DV), `year`, `country`, `country_group`, `iso_code`

> **Basis for `country_group`:** The `country_group` column is a study-defined purposive sampling variable that stratifies the 15 selected countries into three tiers based on their combined income level and governance profile: (1) *Developed* — World Bank High Income economies (World Bank, 2023) with WGI composite scores above the global 75th percentile; (2) *Developing* — World Bank Upper-Middle Income economies with moderate WGI profiles; (3) *Lower Governance* — Lower-Middle Income economies with WGI composite scores below the global median. This stratification maximises variance in both the IV (AI Readiness) and Moderator (WGI) across the sample. Classification sources: World Bank Country Classification System (World Bank, 2023, https://datahelpdesk.worldbank.org/knowledgebase/articles/906519); WGI percentile thresholds from Kaufmann, D., Kraay, A., & Mastruzzi, M. (2010). World Bank Policy Research Working Paper No. 5430.

---

## Step 1 — Descriptive Statistics

Compute for `ai_readiness_score` and `sdg_index_score`:
- Mean, median, standard deviation, min, max
- Compute separately for each country group (Developed, Developing, Lower Governance)
- Compute year-wise means (2020, 2021, 2022, 2023) to observe trends

**Output:** Summary table for both variables across groups and years

---

## Step 2 — Visual Exploration

1. **Scatter plot:** `ai_readiness_score` (x-axis) vs `sdg_index_score` (y-axis)
   - Color-code points by country group
   - Add a linear trend line (OLS fit line)
   - Label each country point

2. **Line plots over time:** One line per country showing AI Readiness and SDG scores across 2020–2023 (two separate plots, side by side)

3. **Box plots:** Distribution of AI Readiness and SDG scores by country group

---

## Step 3 — Correlation Analysis

- Compute Pearson correlation coefficient between `ai_readiness_score` and `sdg_index_score` using the pooled panel data (all 60 observations)
- Report: r value, p-value, 95% confidence interval
- Also compute within-group correlations for each of the 3 country groups separately

**Interpretation guide:**
- |r| > 0.7 → strong correlation
- |r| 0.4–0.7 → moderate correlation
- |r| < 0.4 → weak correlation

---

## Step 4 — Panel Regression Setup

**Model for RQ1 (baseline bivariate model):**

```
SDG_score_it = β0 + β1 * AI_Readiness_it + αi + λt + εit
```

Where:
- `i` = country index (1 to 15)
- `t` = year index (2020 to 2023)
- `αi` = country fixed effect (controls for time-invariant country characteristics)
- `λt` = year fixed effect (controls for global shocks common to all countries)
- `εit` = error term

---

## Step 5 — Pooled OLS (Baseline, no panel structure)

- Run a simple OLS regression of `sdg_index_score` on `ai_readiness_score`
- Report: coefficient (β1), standard error, t-statistic, p-value, R²
- This serves as a naive baseline before applying proper panel methods

---

## Step 6 — Fixed Effects (FE) Panel Regression

- Estimate the within-country effect of AI Readiness on SDG outcomes
- Use entity-demeaned (within) estimator
- Include year fixed effects (two-way FE)
- Report: β1 coefficient, standard error, p-value, R² (within), number of observations, number of countries

**Python library:** `linearmodels` (`PanelOLS` with `EntityEffects` and `TimeEffects`)

---

## Step 7 — Random Effects (RE) Panel Regression

- Estimate the GLS random effects model
- Report: β1 coefficient, standard error, p-value, overall R²

**Python library:** `linearmodels` (`RandomEffects`)

---

## Step 8 — Hausman Test

- Test null hypothesis: random effects are consistent (RE preferred)
- If p < 0.05: reject null → use Fixed Effects
- If p ≥ 0.05: fail to reject null → use Random Effects
- Report which model is selected and why

---

## Step 9 — Cluster-Robust Standard Errors

- Re-run the selected model (FE or RE) with standard errors clustered at the country level
- This accounts for serial correlation within countries over time (important in panel data)

---

## Step 10 — Answering RQ1

Summarize the findings:
- State the direction of the relationship (positive/negative/null)
- Report the coefficient magnitude and statistical significance (p-value and confidence interval)
- Interpret the practical meaning: "A one-unit increase in AI Readiness is associated with a [β1] unit change in SDG Index score"
- Distinguish association from causation (observational data limitation)

---

## Expected Output Files

| File | Content |
|------|---------|
| `outputs/rq1_descriptive_stats.csv` | Summary statistics table |
| `outputs/rq1_scatter_plot.png` | Scatter plot with trend line |
| `outputs/rq1_correlation_results.csv` | Correlation table |
| `outputs/rq1_regression_results.csv` | FE/RE coefficient tables |
| `outputs/rq1_hausman_test.txt` | Hausman test result |
