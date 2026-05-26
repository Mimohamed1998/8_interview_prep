# H3 Analysis Plan

**H3: The quality of governance is a moderately positive variable between AI preparedness and sustainability results.**

**Data required:** `data/3_processed_data/master_features/panel_dataset_2020_2023.parquet`
- Key variables: `ai_readiness_score` (IV), `wgi_composite` (Moderator), `sdg_index_score` (DV), `ai_wgi_interaction` (product term), `year`, `country`, `country_group`, `iso_code`

H3 is the primary hypothesis of this study and is tested using the full moderation model developed in RQ3.

---

## Hypothesis Formulation

- **Null Hypothesis (H0):** β3 = 0 — Governance quality does not moderate the AI readiness → sustainability relationship
- **Alternative Hypothesis (H3):** β3 > 0 — Governance quality positively moderates the AI readiness → sustainability relationship (higher governance amplifies the positive AI-sustainability link)

This is a **one-tailed** test for the interaction coefficient β3.

---

## Step 1 — Confirm Full Moderation Model Setup

The full model from RQ3 must be run first:

```
SDG_score_it = β0 + β1 * AI_Readiness_it + β2 * WGI_it + β3 * (AI_Readiness_it × WGI_it) + αi + λt + εit
```

- Use mean-centered `ai_readiness_centered` and `wgi_centered` to reduce multicollinearity
- Interaction term: `ai_wgi_interaction = ai_readiness_centered × wgi_centered`
- Selected model: Fixed Effects or Random Effects (per Hausman test in RQ3)
- Standard errors clustered at country level

---

## Step 2 — Test the Interaction Coefficient β3

From the full moderation panel model:

- Report β3 (interaction term coefficient)
- Report standard error (SE) for β3
- Compute one-tailed t-statistic: `t = β3 / SE`
- Compute one-tailed p-value: `p = P(T > t)` with appropriate df
- Report 95% one-tailed confidence interval lower bound: `β3 − 1.645 × SE`

**Decision rule:**
- If β3 > 0 AND p < 0.05 (one-tailed) → Reject H0, support H3
- If β3 ≤ 0 OR p ≥ 0.05 → Fail to reject H0, H3 not supported

**Important:** β1 and β2 do not need to be significant for H3 to be tested; only β3 is the hypothesis test for H3.

---

## Step 3 — Simple Slopes Test (Decomposing the Moderation)

To understand the nature of the moderation (not just whether it exists):

1. Define three WGI levels:
   - **Low governance:** WGI = mean − 1 SD
   - **Mean governance:** WGI = mean
   - **High governance:** WGI = mean + 1 SD

2. At each level, compute the conditional effect of AI Readiness on SDG:
   - Conditional slope at Low WGI = β1 + β3 × (mean − 1 SD)
   - Conditional slope at Mean WGI = β1 + β3 × (mean)
   - Conditional slope at High WGI = β1 + β3 × (mean + 1 SD)

3. Test whether each conditional slope is significantly different from zero
   - A positive, significant slope at High WGI and a non-significant slope at Low WGI would be strong evidence for H3

4. **Interaction plot (simple slopes plot):**
   - X-axis: AI Readiness score (continuous)
   - Y-axis: Predicted SDG score
   - Three lines: Low, Mean, and High governance
   - Lines should fan out (diverge) if positive moderation exists:
     - High governance line has a steeper positive slope
     - Low governance line is flatter or near-horizontal

---

## Step 4 — Johnson-Neyman Floodlight Analysis

The Johnson-Neyman technique identifies the exact range of WGI values where the AI Readiness → SDG effect is statistically significant:

1. Compute the WGI threshold value (J-N point) where the conditional AI Readiness effect crosses p = 0.05
2. Report: "The effect of AI Readiness on SDG outcomes is statistically significant (p < 0.05) when governance quality (WGI) is above [threshold value]"
3. **Floodlight plot:**
   - X-axis: WGI composite score (range of observed values)
   - Y-axis: Conditional effect of AI Readiness on SDG
   - Shade the region where the effect is statistically significant (p < 0.05)
   - Mark the J-N point with a vertical dashed line

---

## Step 5 — Practical Significance Assessment

Beyond statistical significance, evaluate practical significance:

- At High governance vs Low governance, by how many SDG points does a 10-unit increase in AI Readiness differ?
- Express this in terms of ranking: would this difference move a country's SDG ranking by [X] positions?
- Compare effect size when WGI is high (f² or partial η²) vs when WGI is low

---

## Step 6 — Robustness Checks for H3

1. **Alternative interaction specification:** Test the non-centered version of the interaction; coefficients will differ but β3 should remain the same sign and significance
2. **Split-sample validation:** Divide the 15 countries into two groups by WGI median; run AI Readiness → SDG regression in each half; compare slopes (the high-WGI half should show a stronger slope)
3. **Year-by-year interaction:** Run the full moderation model as a cross-section for each year separately (2020, 2021, 2022, 2023); check if β3 is consistently positive across years
4. **Bootstrap confidence interval for β3:** Run 1,000 bootstrap samples; report the bootstrapped 95% CI for β3; this is more reliable than normal-theory CI with small N=60

---

## Step 7 — Reporting H3 Results

Produce a concise results table for the full moderation model:

| Predictor | β | SE | t-stat | p-value (1-tail) | 95% CI |
|-----------|---|---|--------|-----------------|--------|
| AI Readiness (β1) | | | | | |
| WGI Composite (β2) | | | | | |
| AI Readiness × WGI (β3) | | | | | |
| Constant | | | | | |

And the simple slopes table:

| WGI Level | Conditional AI Readiness Effect | SE | t-stat | p-value |
|-----------|--------------------------------|-----|--------|---------|
| Low (mean − 1 SD) | | | | |
| Mean | | | | |
| High (mean + 1 SD) | | | | |

**Narrative conclusion example:**
> "The interaction term between AI Readiness and WGI composite was statistically significant and positive (β3 = [X], SE = [X], t = [X], p = [X], one-tailed), supporting H3. Governance quality positively moderates the relationship between AI preparedness and sustainability outcomes. Simple slopes analysis revealed that the positive effect of AI Readiness on SDG scores was significant in high-governance contexts (β = [X], p = [X]) but not in low-governance contexts (β = [X], p = [X]). Johnson-Neyman analysis indicated that governance must exceed a WGI score of [X] for AI Readiness to significantly predict sustainability gains."

---

## Expected Output Files

| File | Content |
|------|---------|
| `outputs/h3_moderation_model_results.csv` | Full model coefficient table |
| `outputs/h3_simple_slopes_table.csv` | Conditional AI Readiness effects at 3 WGI levels |
| `outputs/h3_interaction_plot.png` | Simple slopes plot (3-line interaction visualization) |
| `outputs/h3_johnson_neyman_plot.png` | Floodlight significance plot |
| `outputs/h3_bootstrap_ci.csv` | Bootstrapped CI for β3 |
| `outputs/h3_robustness_year_by_year.csv` | β3 for each year cross-section |
