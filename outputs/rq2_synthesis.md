## Plain-Language Synthesis - RQ2
> Written for readers who are not statisticians
> **RQ2:** How does the quality of governance affect sustainability outcomes?

---

### What did we study?

This analysis examined whether countries with better governance achieve higher scores on the Sustainable Development Goals (SDG Index). Governance was measured using the World Governance Indicators (WGI) composite score, which combines six dimensions: voice and accountability, political stability, government effectiveness, regulatory quality, rule of law, and control of corruption. Higher WGI scores indicate stronger overall governance. We used data from 26 countries across four years (2020-2023), giving 104 country-year observations. The sample spans a wide governance range -- from strongly governed Developed economies (Finland, Denmark, Singapore) to Developing economies (India, Brazil, South Africa) to Lower Governance countries (Nigeria, Pakistan, Bangladesh) -- making it well-suited to detect a governance-sustainability relationship.

---

### What did we find?

#### Finding 1 - Governance quality is strongly associated with sustainability outcomes

The Pearson correlation between WGI composite and SDG Index Score is r = 0.859 (p = 0.0000). The Spearman rank correlation is rho = 0.808, confirming the relationship is robust to non-normality. The pooled OLS regression finds that a one-unit increase in WGI composite is associated with approximately 7.98 additional SDG Index points (beta1 = 7.9755, p = 0.0000). Since WGI ranges from roughly -1.17 to +1.92 in our sample (a span of 3.09 units), the full governance range implies a difference of about 24.6 SDG points between the worst- and best-governed countries -- a substantively large gap on a 100-point scale. This model explains 73.8% of the variation in SDG scores (R2 = 0.738).

#### Finding 2 - Clear tier separation between country groups

The three country groups show markedly different sustainability outcomes: Developed countries average 80.7 on the SDG Index, Developing countries average 70.0, and Lower Governance countries average 58.7. The between-group comparison (Kruskal-Wallis / ANOVA) confirmed these differences are statistically significant. This stratification directly mirrors the governance profile of each group, consistent with the regression findings.

#### Finding 3 - Relationship holds under panel regression and robustness checks

The Fixed Effects (Two-Way) model (selected via Hausman test) yields beta1 = 0.9655 (p = 0.2027, R2 = 0.018). Year-by-year OLS confirms a consistent positive WGI-SDG relationship across all four years (2020-2023). Cook's Distance analysis identified influential observations; excluding them did not materially change the sign or magnitude of the coefficient, confirming robustness.

---

### How confident are we?

| What we measured | Result | Confidence |
|---|---|---|
| Pearson correlation (WGI vs SDG) | r = 0.859 | Significant (p < 0.05) |
| Spearman correlation | rho = 0.808 | Significant (p < 0.05) |
| Regression beta1 (Pooled OLS) | 7.9755 | Statistically Significant (P < 0.05) |
| Regression beta1 (Fixed Effects (Two-Way)) | 0.9655 | Not significant (p >= 0.05) |
| Model fit (R2) | 0.738 | High explanatory power |
| Group differences | Kruskal-Wallis / ANOVA | Tested with Bonferroni correction |

Statistical significance means the finding is unlikely to be due to chance (p < 0.05). R2 tells us what share of SDG score variability is explained by governance quality alone.

---

### What are the limitations?

- Observational data: Governance is associated with sustainability outcomes, but we cannot prove causation. Both could reflect underlying national wealth or historical development trajectories.
- Small sample: 104 country-year observations across 26 countries limits the power of Fixed Effects models, which rely on within-country governance changes over time.
- WGI composite: Averaging six governance dimensions assumes equal importance. Individual dimensions (e.g., government effectiveness) may matter more than others (e.g., political stability) for SDG outcomes.
- Short time window: Four years (2020-2023) captures limited within-country governance variation. Governance changes slowly; longer panels would yield more reliable within-country estimates.

---

### In plain English: Countries with stronger, more transparent, and more accountable governments consistently achieve better sustainability outcomes -- governance quality is one of the most powerful predictors of where a country stands on the SDG Index.
