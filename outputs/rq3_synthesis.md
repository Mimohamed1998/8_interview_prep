## 📊 Plain-Language Synthesis — RQ3 Analysis
> Written for readers who are not statisticians

---

### What did we study?
We asked: does good governance change how effectively AI readiness translates into better sustainability outcomes?
Using panel data on 26 countries (2020–2023, n=104 observations), we built an interaction regression model
where governance quality (WGI composite) was tested as a *moderator* of the AI readiness → SDG score relationship.

---

### What did we find?

#### Finding 1 — The interaction term (β₃) was not statistically significant
The key coefficient in the moderation model was β₃ = -0.0344 (SE = 0.0198, p = 0.0864).
This means the combined effect of governance × AI readiness was not statistically significant.
The evidence does not establish a clear moderating role for governance in this sample and time period.

#### Finding 2 — Subgroup regressions corroborate the pattern
When we split countries into High Governance (top 25% of WGI) and Low Governance (bottom 25%) groups
and ran separate regressions, the AI readiness slope was:
- **High Governance countries:** β₁ = -1.0453 (p = 0.0039)
- **Low Governance countries:**  β₁ = 0.6122 (p = 0.0000)
Notably, the slope difference between groups was modest, suggesting governance may not decisively alter the AI-SDG link in this dataset.

#### Finding 3 — Johnson-Neyman floodlight shows the significance threshold
The Johnson-Neyman analysis identified that the AI readiness → SDG relationship is statistically significant
at governance level WGI ≥ 0.21.
This provides a practical governance threshold: countries must achieve at least this WGI score to reliably
convert AI readiness into measurable sustainability gains.

#### Finding 4 — The full moderation model (M3) improves fit over the baseline
Adding governance and the interaction term raised R² by ΔR² = 0.1096 compared to the AI-only model (M1).
The F-change test gave F = 28.2754 (p = 0.0000),
indicating the full moderation model significantly improves predictive fit.

---

### How confident are we?

| What we measured | Result | Confidence |
|-----------------|--------|------------|
| Interaction effect β₃ | -0.0344 (p = 0.0864) | Not significant |
| Subgroup contrast (high vs low WGI) | High β₁ = -1.045 vs Low β₁ = 0.612 | Strong contrast |
| Model fit improvement (ΔR²) | 0.1096 | Significant (p < 0.05) |
| Sample size | 104 obs / 26 countries | Small-N — interpret cautiously |

> **Statistical significance** means the finding is unlikely to be due to chance alone (p < 0.05).

---

### What are the limitations?

- **Observational data:** We can show association, not causation. Both AI readiness and governance may be driven by a third factor (national wealth, historical institutions).
- **Sample size:** 26 countries × 4 years = 104 observations. Panel models with fixed effects lose degrees of freedom, reducing power to detect interaction effects.
- **Short time span:** Four years (2020–2023) is insufficient to capture long-run governance → AI → SDG dynamics.
- **WGI aggregation:** The composite WGI averages six dimensions; different governance sub-dimensions may moderate the relationship differently.

---

### In plain English:
While theory predicts governance should amplify AI readiness benefits for sustainability, this study found the interaction effect was not statistically significant across the 26-country sample — suggesting either that the moderating role of governance is subtle, that sample size limits detection, or that other factors play a larger role.
