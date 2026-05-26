## 📊 Plain-Language Synthesis
> *Written for readers who are not statisticians*

---

### What did we study?

We examined whether countries with better governance quality — measured by the World Bank's Worldwide Governance Indicators (WGI) composite score — also achieve higher sustainability outcomes, as measured by the SDG Index score. Using a panel of 26 countries across four years (2020–2023), we applied Fixed Effects panel regression (the most rigorous method for this type of data, preferred by the Hausman test: χ² = 17.60, p < 0.0001) to ask: *after accounting for everything permanently different between countries, does a change in governance quality within a country predict a corresponding change in its sustainability score?*

---

### What did we find?

#### Finding 1 — The governance–sustainability gradient is striking across countries
Across all 26 countries, better-governed countries consistently score higher on sustainability. The pooled Pearson correlation is r = 0.86 (p < 0.001) — governance quality explains roughly 74% of the variation in SDG scores. At the country level, the Spearman rank correlation is ρ = 0.81 (p < 0.001, 95% CI [0.63, 0.91]): rank a country by governance quality and you nearly rank it by sustainability performance.

#### Finding 2 — The three governance-tier gradient is perfectly ordered
Countries in the *Developed* governance tier averaged an SDG score of **80.7**, compared to **70.0** in the *Developing* tier and **58.7** in the *Lower Governance* tier — a 22-point spread. This monotonically decreasing gradient is exactly what H2 predicts. A Kruskal-Wallis test confirms these differences are not due to chance (H = 82.2, p < 0.0001), and all three pairwise comparisons are significant after Bonferroni correction.

#### Finding 3 — The formal Fixed Effects test is directionally correct but marginally non-significant
The Fixed Effects regression coefficient is β₁ = 0.9655 (SE = 0.7512, t = 1.2853, p = 0.1008 one-tailed). The direction is consistent with H2 (β₁ > 0), but the result just misses the α = 0.05 threshold. The key explanation: WGI scores change very little within a single country over four years — the FE estimator, which is designed to detect within-country year-to-year changes, has limited power in a short four-year panel. Year-by-year cross-sectional regressions confirm the coefficient is positive in all four years (2020–2023).

---

### How confident are we?

| What we measured | Result | Confidence |
|-----------------|--------|------------|
| FE within-country β₁ (wgi_composite) | 0.9655 (p = 0.10, one-tail) | Marginal — direction correct, borderline significance |
| Cross-sectional Pearson r | 0.86 (p < 0.001) | Very strong |
| Country-level Spearman ρ | 0.81 (p < 0.001) | Very strong |
| Group gradient (K-W test) | H = 82.2, p < 0.0001 | Extremely strong |
| Effect size (Cohen's f², within-FE) | 0.018 (small) | Small within-country |
| Alternative WGI scaling robustness | Significant under both raw & percentile rank | Scale-independent |
| Year-by-year consistency | β₁ positive in all 4 years | Directionally robust |

> **Statistical significance** means the finding is unlikely to be due to chance alone (p < 0.05).
> **Effect size** tells us whether the finding is practically meaningful, not just statistically detectable.

---

### What are the limitations?

- **Short panel / within-country FE power:** The FE model strips out all between-country differences. Because WGI changes slowly within a single country over a 4-year window, the estimator has limited statistical power. A 10–15 year panel would likely yield a significant FE estimate.
- **Observational data:** Governance quality is *associated* with sustainability, but we cannot prove causation. Both could be driven by national wealth or historical institutional development.
- **Sample size:** With 104 country-year observations (26 countries × 4 years), the FE estimate sits at p = 0.10 — marginally outside conventional significance. A slightly larger or longer sample could tip this result.
- **Composite governance measure:** WGI is an average of six sub-dimensions. Individual dimensions (voice & accountability, rule of law, etc.) may have heterogeneous relationships with sustainability that are masked in the composite.

---

### In plain English: Countries with stronger governance consistently achieve higher sustainability scores — the pattern is clear and robust in every cross-sectional test, but the most conservative within-country analysis (Fixed Effects over just four years) falls just short of the 5% significance threshold, meaning we cannot formally rule out chance for within-country year-to-year governance changes in this short window.
