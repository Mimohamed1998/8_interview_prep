# RQ3 Analysis Plan

**RQ3: Does the quality of governance moderate the AI readiness and sustainability outcomes relationship?**

**Data required:** `data/3_processed_data/master_features/panel_dataset_2020_2023.parquet`
- Key variables: `ai_readiness_score` (IV), `wgi_composite` (Moderator), `sdg_index_score` (DV), `year`, `country`, `country_group`, `iso_code`

This is the central research question of the study. It tests whether WGI acts as a moderator in the AI readiness → SDG outcomes pathway.

---

## Step 1 — Conceptual Model

The moderation model specifies:

```
SDG_score = f(AI_Readiness, WGI, AI_Readiness × WGI)
```

- If the interaction term (AI_Readiness × WGI) is statistically significant → governance moderates the AI-sustainability relationship
- A positive significant interaction → governance amplifies the positive effect of AI readiness on sustainability

---

## Step 2 — Variable Preparation

Before building the interaction term:

1. **Mean-center both continuous predictors** to reduce multicollinearity:
   - `ai_readiness_centered = ai_readiness_score − mean(ai_readiness_score)`
   - `wgi_centered = wgi_composite − mean(wgi_composite)`

2. **Create interaction term:**
   - `ai_wgi_interaction = ai_readiness_centered × wgi_centered`

3. Verify variance inflation factor (VIF) for all predictors; VIF < 10 is acceptable

---

## Step 3 — Full Moderation Panel Regression Model

**Model specification:**

```
SDG_score_it = β0 + β1 * AI_Readiness_it + β2 * WGI_it + β3 * (AI_Readiness_it × WGI_it) + αi + λt + εit
```

Where:
- `β1` = main effect of AI Readiness (when WGI = mean)
- `β2` = main effect of Governance Quality (when AI Readiness = mean)
- `β3` = moderation coefficient (the key coefficient for RQ3)
- `αi` = country fixed effect
- `λt` = year fixed effect

---

## Step 4 — Model Estimation Steps

### 4a — Pooled OLS with interaction (baseline reference)
- Run OLS with all three terms: AI Readiness, WGI, and interaction
- Report all three coefficients with p-values and R²
- Note: ignores panel structure

### 4b — Fixed Effects panel model with interaction
- `PanelOLS` with `EntityEffects` and `TimeEffects`
- Use centered variables and interaction term
- Report: β1, β2, β3, SE for each, p-values, within-R²
- Cluster standard errors at country level

### 4c — Random Effects panel model with interaction
- `RandomEffects` GLS estimator
- Report the same coefficient set

### 4d — Hausman Test
- Decide between FE and RE for the full interaction model
- Report test result and model selection decision

---

## Step 5 — Interpreting the Interaction Term (β3)

| β3 sign | p-value | Interpretation |
|---------|---------|----------------|
| Positive | < 0.05 | Higher governance amplifies the positive AI-sustainability link (supports H3) |
| Negative | < 0.05 | Higher governance weakens the AI-sustainability link (unexpected result) |
| Any | ≥ 0.05 | No significant moderation; governance does not moderate the relationship |

---

## Step 6 — Simple Slopes Analysis

To visualize the moderation effect:

1. Define three governance levels:
   - Low WGI: mean − 1 SD
   - Mean WGI: mean
   - High WGI: mean + 1 SD

2. Compute predicted SDG scores at each level of WGI, across the range of AI Readiness scores

3. Plot the **interaction plot** (simple slopes plot):
   - X-axis: AI Readiness score
   - Y-axis: Predicted SDG Index score
   - Three lines: Low, Mean, and High governance
   - Include confidence bands

4. Test simple slopes at each WGI level for significance (Johnson-Neyman technique or spotlight analysis)

---

## Step 7 — Regions of Significance (Johnson-Neyman Analysis)

- Identify the range of WGI values at which the AI Readiness → SDG relationship is statistically significant
- This tells us: "governance must be at least [X] for AI readiness to significantly predict sustainability"
- Plot floodlight graph showing significance region

---

## Step 8 — Country Group Analysis (Governance-Stratified Subgroup Regression)

To add substantive insight and validate the moderation finding with a complementary non-parametric approach.

---

### 8a — Basis for Country Classification

**Source of governance scores:** Countries are classified using their **mean `wgi_composite` score across the study period (2020–2023)**, computed from the **World Bank Worldwide Governance Indicators (WGI)** dataset — the same dataset used to construct the moderator variable throughout this study.

> **Primary data source:** Kaufmann, D., Kraay, A., & Mastruzzi, M. (2010). *The Worldwide Governance Indicators: Methodology and Analytical Issues*. World Bank Policy Research Working Paper No. 5430. Washington, DC: The World Bank Group. https://doi.org/10.1596/1813-9450-5430

> **Live database:** World Bank Group. (2024). *Worldwide Governance Indicators (WGI), 2020–2023* [Dataset]. Retrieved from https://www.worldbank.org/en/publication/worldwide-governance-indicators

**Why WGI?** The WGI is the most widely used cross-national governance index in empirical research, covering 200+ countries annually since 1996. It is produced by the World Bank and aggregates data from 30+ data sources across six governance dimensions:

| WGI Dimension | What it measures |
|---|---|
| **Voice & Accountability (VA)** | Citizens' participation in government selection; freedom of expression and press |
| **Political Stability & Absence of Violence (PV)** | Likelihood of political instability, terrorism, or unconstitutional government changes |
| **Government Effectiveness (GE)** | Quality of public services, civil service competence, and policy implementation |
| **Regulatory Quality (RQ)** | Government's ability to formulate and implement sound policies enabling private sector development |
| **Rule of Law (RL)** | Confidence in and adherence to rules: property rights, contract enforcement, courts, police |
| **Control of Corruption (CC)** | Extent to which public power is exercised for private gain; state capture by elites |

Each dimension is scored on a standardised scale from **−2.5 (weakest) to +2.5 (strongest)**. The `wgi_composite` used in this study is the **equally-weighted mean across all six dimensions** per country-year.

---

### 8b — Grouping Rule (Data-Driven Quartile Threshold)

Countries are assigned to governance groups using the **75th and 25th percentile thresholds** of the mean `wgi_composite` score computed across all countries in the panel:

- **High Governance group:** Countries with mean `wgi_composite` ≥ 75th percentile of the panel
- **Low Governance group:** Countries with mean `wgi_composite` ≤ 25th percentile of the panel
- Middle-quartile countries are **excluded** from the subgroup comparison to maximise governance contrast

**Literature basis for quartile-based classification:**

> 1. **UNDP precedent:** The United Nations Development Programme (UNDP) classifies all countries into Very High, High, Medium, and Low Human Development using quartile thresholds of the Human Development Index (HDI) — the most widely cited country-classification framework in international development research (UNDP, 2023, *Human Development Report*. https://hdr.undp.org).

> 2. **Moderation analysis methodology:** Subgroup regression stratified at the quartile thresholds of the moderator is a standard robustness check for interaction effects, recommended by Aiken, L. S., & West, S. G. (1991). *Multiple Regression: Testing and Interpreting Interactions*. Thousand Oaks, CA: Sage Publications. Quartile thresholds (rather than ±1 SD) are preferred when the moderator's distribution is non-normal or skewed, as is common with governance scores across heterogeneous country panels.

> 3. **WGI percentile rank as a built-in classification tool:** The World Bank WGI database itself publishes a **percentile rank** (0–100) for each country alongside the composite estimate score. Using the 25th and 75th percentile thresholds therefore aligns directly with the classification logic embedded in the WGI methodology (Kaufmann et al., 2010).

> 4. **Precedent in governance-development literature:** Quartile-based WGI classification has been used in peer-reviewed panel studies examining governance as a moderator of economic and development outcomes (e.g., Hanif et al., 2019, *Energy Policy*, 133, 110872; Isaksson, 2011, *Journal of Development Studies*, 47(10), 1547–1566).

**Decision rule applied programmatically:**
```python
p75 = df.groupby('country')['wgi_composite'].mean().quantile(0.75)
p25 = df.groupby('country')['wgi_composite'].mean().quantile(0.25)

high_gov_countries = countries where mean_wgi >= p75   # top quartile
low_gov_countries  = countries where mean_wgi <= p25   # bottom quartile
```
> The specific countries in each group are determined from the data — not pre-selected — and must be reported in the thesis after running the classification step.

**Typical country composition based on WGI literature (to be confirmed from your data):**

| Group | Typical members | Approx. mean WGI range |
|---|---|---|
| High Governance (≥ P75) | Denmark, Finland, Norway, Singapore, New Zealand, Netherlands, Germany | +1.3 to +2.0 |
| Low Governance (≤ P25) | Nigeria, Pakistan, Bangladesh, Yemen, Myanmar, Sudan, Cambodia | −0.8 to −1.5 |

> **Note:** This table is illustrative. Report the actual country list and WGI scores from your dataset in the thesis.

---

### 8c — Analysis Steps

1. Compute mean `wgi_composite` per country across 2020–2023; assign quartile group label
2. Run **separate OLS/FE regressions** of `sdg_index_score ~ ai_readiness_score` for:
   - High Governance sub-group
   - Low Governance sub-group
3. Compare the magnitude and significance of **β₁** (AI Readiness slope) across both groups
4. Report: coefficient, SE, p-value, and within-R² for each subgroup regression
5. **Expected pattern:** larger, more significant β₁ in the High Governance group — consistent with the moderation hypothesis (H3) and corroborating the interaction term β₃ from Step 4b

---

## Step 9 — Model Comparison

Compare three nested models using F-test and AIC/BIC:
- **Model 1 (RQ1 base):** SDG ~ AI Readiness + FE
- **Model 2 (RQ2 base):** SDG ~ WGI + FE
- **Model 3 (RQ3 full):** SDG ~ AI Readiness + WGI + (AI_Readiness × WGI) + FE

Report improvement in R² and F-test significance when adding the interaction term to assess whether moderation meaningfully improves model fit.

---

## Step 10 — Answering RQ3

State clearly:
- Whether β3 is statistically significant and its direction
- Whether governance is a significant moderator (yes/no, with evidence)
- The nature of the moderation: amplifying or dampening
- At what governance threshold the AI-sustainability link becomes significant (from Johnson-Neyman)
- Practical implication: countries should achieve a minimum governance quality of [X] to realize AI readiness benefits for sustainability

---

## Expected Output Files

| File | Content |
|------|---------|
| `outputs/rq3_vif_check.csv` | VIF values for predictors |
| `outputs/rq3_full_model_results.csv` | Full moderation model coefficients |
| `outputs/rq3_interaction_plot.png` | Simple slopes interaction plot |
| `outputs/rq3_johnson_neyman.png` | Floodlight significance plot |
| `outputs/rq3_model_comparison.csv` | Model 1 vs 2 vs 3 AIC/BIC/R² table |
| `outputs/rq3_subgroup_regression.csv` | Separate regressions by governance group |
