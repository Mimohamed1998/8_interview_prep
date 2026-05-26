# RQ2 Analysis Plan

**RQ2: How does the quality of governance affect the sustainability outcomes?**

**Data required:** `data/3_processed_data/master_features/panel_dataset_2020_2023.parquet`
- Key variables: `wgi_composite` (IV), `sdg_index_score` (DV), `year`, `country`, `country_group`, `iso_code`

> **Basis for `country_group`:** The `country_group` column is a study-defined purposive sampling variable that stratifies the 15 selected countries into three tiers based on their combined income level and governance profile: (1) *Developed* — World Bank High Income economies (World Bank, 2023) with WGI composite scores above the global 75th percentile; (2) *Developing* — World Bank Upper-Middle Income economies with moderate WGI profiles; (3) *Lower Governance* — Lower-Middle Income economies with WGI composite scores below the global median. This stratification maximises variance in both the IV (WGI) and the DV (SDG) across the sample. Classification sources: World Bank Country Classification System (World Bank, 2023, https://datahelpdesk.worldbank.org/knowledgebase/articles/906519); WGI percentile thresholds from Kaufmann, D., Kraay, A., & Mastruzzi, M. (2010). World Bank Policy Research Working Paper No. 5430.

---

## Step 1 — Descriptive Statistics for Governance Quality

Compute for `wgi_composite`:
- Mean, median, standard deviation, min, max for the full sample
- Breakdown by country group (Developed, Developing, Lower Governance)
- Year-wise averages (2020–2023) to identify trends
- Rank countries by their average WGI composite score

**Output:** Table showing WGI profile of all 15 countries across 4 years

---

## Step 2 — Governance Quality Profile Visualization

1. **Bar chart (or heatmap):** Average WGI composite score by country, sorted descending
   - Color-code bars by country group

2. **Line plot:** Year-wise mean WGI composite by country group (3 lines: Developed, Developing, Lower Governance) from 2020–2023

3. **Radar/spider chart (optional):** Show all 6 individual WGI dimensions for one representative country per group (e.g., Finland vs India vs Nigeria)

4. **Box plot:** Distribution of WGI scores by country group (shows spread within groups)

---

## Step 3 — Correlation Analysis

- Pearson correlation between `wgi_composite` and `sdg_index_score` (pooled, n=60)
- Report: r, p-value, 95% confidence interval
- Also compute within-group correlations

---

## Step 4 — Panel Regression Setup

**Model for RQ2 (bivariate governance model):**

```
SDG_score_it = β0 + β1 * WGI_it + αi + λt + εit
```

Where:
- `i` = country index (1 to 15)
- `t` = year index (2020 to 2023)
- `αi` = country fixed effect
- `λt` = year fixed effect
- `εit` = error term

---

## Step 5 — Pooled OLS (Baseline)

- Simple OLS regression of `sdg_index_score` on `wgi_composite`
- Report: β1, standard error, t-statistic, p-value, R²
- Note: this ignores panel structure and serves only as a reference

---

## Step 6 — Fixed Effects (FE) Panel Regression

- Within-country estimation: how do changes in governance quality within a country over time affect its SDG score
- Include year fixed effects (two-way FE)
- Report: β1 coefficient, SE, p-value, within-R², number of observations, number of groups

**Python library:** `linearmodels` (`PanelOLS` with `EntityEffects` and `TimeEffects`)

---

## Step 7 — Random Effects (RE) Panel Regression

- GLS random effects model
- Report: β1 coefficient, SE, p-value, overall R²

---

## Step 8 — Hausman Test

- Test which model (FE vs RE) is appropriate
- If p < 0.05 → Fixed Effects preferred
- If p ≥ 0.05 → Random Effects preferred
- Report test statistic, degrees of freedom, p-value, and decision

---

## Step 9 — Cluster-Robust Standard Errors

- Apply country-level clustering to the selected model's standard errors
- This corrects for within-country autocorrelation over 4 time periods

---

## Step 10 — Between-Group Comparison

To answer "How does governance affect sustainability?" more richly:

- Compute mean SDG score for each WGI quartile group (low, medium-low, medium-high, high governance)
- ANOVA or Kruskal-Wallis test to check if SDG scores differ significantly across governance quality groups
- Post-hoc pairwise comparisons if ANOVA is significant

---

## Step 11 — Answering RQ2

Summarize the findings:
- Direction and magnitude of governance → sustainability relationship
- Report β1 coefficient with confidence interval and p-value
- Interpret: "A one-unit increase in governance quality is associated with a [β1] point change in SDG score"
- Discuss which governance dimension (if individual WGI dimensions are analyzed) has the strongest association
- Note the observational limitation (association, not causation)

---

## Expected Output Files

| File | Content |
|------|---------|
| `outputs/rq2_descriptive_stats.csv` | WGI summary statistics by country and group |
| `outputs/rq2_wgi_bar_chart.png` | WGI composite bar chart by country |
| `outputs/rq2_scatter_plot.png` | WGI vs SDG scatter plot |
| `outputs/rq2_correlation_results.csv` | Correlation table |
| `outputs/rq2_regression_results.csv` | FE/RE coefficient tables |
| `outputs/rq2_hausman_test.txt` | Hausman test result |
| `outputs/rq2_group_comparison.csv` | ANOVA/Kruskal-Wallis results by governance group |
