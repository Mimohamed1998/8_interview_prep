# H1 Synthesis - AI Readiness -> Sustainability Performance

## Hypothesis
**H1:** AI preparedness has a positive impact on sustainability performance.
**H0:** beta1 <= 0  |  **Test:** one-tailed t-test, alpha=.05
**Selected model:** Fixed Effects (Two-Way) per Hausman test (chi2=209.66, p<.001) from RQ1.

---

## Step 1 - Primary Hypothesis Test

N = 104 observations (26 countries x 4 years).

| Model | beta1 | SE | t-stat | p (1-tail) | 95% CI lower (1-tail) | Decision |
|-------|-------|----|--------|-----------|----------------------|----------|
| Pooled OLS | 0.4589 | 0.0338 | 13.5799 | 0.0000 | 0.4033 | Reject H0 |
| **Fixed Effects (SELECTED)** | **0.0206** | **0.0157** | **1.3149** | **0.0963** | **-0.0052** | **Fail to reject H0** |
| Random Effects | 0.0584 | 0.0155 | 3.7789 | 0.0001 | 0.0330 | Reject H0 |

**Interpretation:** The Fixed Effects model yields beta1 = 0.0206 (SE=0.0157, t=1.3149, p_1tail=0.0963). The coefficient is **positive** (consistent with H1) but does not reach alpha=.05 once country fixed effects and time trends are absorbed. Pooled OLS beta1=0.4589 is significant but inadmissible given Hausman test mandating FE.

---

## Step 2 - Effect Size

- **R2 (FE within):** 0.0458
- **Cohen's f2:** 0.0480 -> **small effect** (small>=0.02, medium>=0.15, large>=0.35)
- **Standardised beta1 (z-scored FE):** 0.0375 (SE=0.0285)

---

## Step 3 - Robustness Checks

| Check                                 |   beta1 |     SE |   t_stat |   p_1tail | Sign_consistent   |
|:--------------------------------------|--------:|-------:|---------:|----------:|:------------------|
| Outliers excl (Cook D>4/n; removed 7) |  0.0192 | 0.0159 |   1.2072 |    0.1158 | Yes               |
| Year 2020 OLS                         |  0.4485 | 0.0576 |   7.7921 |    0      | Yes               |
| Year 2021 OLS                         |  0.4552 | 0.0562 |   8.0986 |    0      | Yes               |
| Year 2022 OLS                         |  0.4568 | 0.0662 |   6.9049 |    0      | Yes               |
| Year 2023 OLS                         |  0.4904 | 0.068  |   7.2166 |    0      | Yes               |
| Group Developed OLS                   | -0.7582 | 0.1708 |  -4.4392 |    1      | No                |
| Group Developing OLS                  |  0.1342 | 0.0535 |   2.5076 |    0.0083 | Yes               |
| Group Lower Governance OLS            |  0.3875 | 0.1232 |   3.1451 |    0.0024 | Yes               |
| Lagged AI(t)->SDG(t+1) OLS            |  0.4472 | 0.0332 |  13.4691 |    0      | Yes               |

---

## Overall Conclusion on H1

The Fixed Effects panel regression reveals a **positive but not statistically significant** association between AI Readiness and SDG Index scores (beta1=0.0206, SE=0.0157, t=1.3149, p_1tail=0.0963, alpha=.05). The positive sign is consistent with H1 and robust to outlier exclusion and year-by-year cross-sections.

**Recommended thesis statement:**
> 'The Fixed Effects panel regression revealed a positive but non-significant association between AI Readiness and SDG Index scores (beta1=0.0206, SE=0.0157, t=1.3149, p=0.0963, one-tailed, alpha=.05). While the direction is consistent with H1, the evidence does not meet the significance threshold once country-level heterogeneity is removed, suggesting that cross-country structural differences in AI preparedness drive the AI-SDG correlation more than within-country temporal change over 2020-2023.'

---

## Output Files

| File | Description |
|------|-------------|
| h1_hypothesis_test_table.csv | beta1, SE, t, p (1- and 2-tail) for all three models |
| h1_coefficient_plot.png      | beta1 +/- 95% CI across Pooled OLS, FE, RE |
| h1_robustness_checks.csv     | Outlier-excluded, year-by-year, group-level, lagged |
| h1_scatter_annotated.png     | Scatter of AI Readiness vs SDG with fitted line |
| h1_year_panel.png            | Four cross-sectional scatter panels (2020-2023) |