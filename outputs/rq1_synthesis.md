## 📊 Plain-Language Synthesis — RQ1
> *Does AI preparedness have any influence on sustainability outcomes?*  
> *Written for readers who are not statisticians*  
> Generated: 2026-05-25

---

### What did we study?

We examined whether countries that are better prepared for Artificial Intelligence (AI) also perform better on the United Nations' Sustainable Development Goals (SDGs) — a global scorecard measuring progress on health, education, clean energy, poverty reduction, and more. We used data from 26 countries across four years (2020–2023), giving us 104 country-year observations in total. The analysis moved from simple summary statistics through formal statistical models that control for the unique characteristics of each country and each year.

---

### What did we find?

#### Finding 1 — Countries with higher AI readiness consistently score higher on sustainability

Across all 104 observations, AI Readiness Score and SDG Index Score are strongly and positively correlated (Pearson r = 0.835, p < 0.001). In plain terms: countries that have invested more in AI infrastructure, skills, and governance tend to score substantially better on the UN's sustainability index. Every 10-point increase in AI readiness is associated with roughly a 4.6-point improvement in SDG score (Pooled OLS: β₁ = 0.459, SE = 0.034, p < 0.001, R² = 0.70). This means AI readiness alone explains about 70% of the variation in sustainability scores across countries and years.

#### Finding 2 — The relationship is driven by differences between countries, not by change within a single country over time

When we apply Fixed Effects panel regression — which controls for each country's unique characteristics and looks only at *changes over time within a country* — the effect shrinks to β₁ = 0.0206 and becomes marginally insignificant (p = 0.193). This tells us that between 2020 and 2023, year-to-year improvements in AI readiness within a country were not consistently followed by equivalent improvements in SDG scores in the same short window. The Hausman test (χ² = statistically decisive, p < 0.05) confirmed that Fixed Effects is the more appropriate model. The pooled correlation is therefore largely a *cross-sectional* pattern: nations that already had high AI capability also happened to have high sustainability performance — not that building AI readiness *caused* short-run SDG improvements.

#### Finding 3 — Country group differences are stark

Developed countries (e.g., Finland, Denmark, Singapore) averaged an AI Readiness Score of 77.4 and an SDG score of 80.8. Lower Governance countries (e.g., Nigeria, Bangladesh, Pakistan) averaged AI Readiness of 36.8 and SDG of 58.7. Within-group correlations paint a nuanced picture: within the Developed group, higher AI readiness is *negatively* associated with SDG scores (r = -0.584), possibly because highly similar countries show ceiling effects or policy trade-offs. Within Developing (r = 0.377) and Lower Governance (r = 0.557) countries, the positive association holds.

---

### How confident are we?

| What we measured | Result | Confidence |
|-----------------|--------|------------|
| Pooled AI-SDG correlation | r = 0.835, 95% CI [0.765, 0.885] | Very high — significant (p < 0.001) |
| Pooled OLS effect (β₁) | 0.459 per 1-unit AI score | Very high — significant (p < 0.001) |
| Fixed Effects within-country β₁ | 0.0206 per 1-unit AI score | Moderate — marginally insignificant (p = 0.193) |
| Cross-sectional pattern strength | R² = 0.70 (Pooled OLS) | Large effect — pooled model explains 70% of variance |
| Hausman test (model selection) | FE preferred | Statistically decisive (p < 0.05) |

> **Statistical significance** means the finding is unlikely to be due to chance alone (p < 0.05).  
> **Effect size** (r = 0.835) is classified as *large* (|r| > 0.70 = strong).

---

### What are the limitations?

- **Observational data:** We can show that AI readiness is *associated* with SDG performance, but we cannot prove that one *causes* the other. A third factor — such as overall national wealth or institutional quality — likely drives both.
- **Short time horizon:** Four years (2020–2023) is a narrow window. SDG improvements from AI investments may take a decade or more to materialise; the panel FE models cannot detect long-run effects.
- **Sample composition:** With 26 countries purposively selected to represent governance tiers, results are directional indicators rather than global generalisations.
- **Fixed Effects limitation:** By design, FE removes all stable country differences. Since AI readiness changes slowly, little within-country variation remains for the model to estimate — this makes the FE estimate imprecise even if the true long-run effect is real.

---

### In plain English

Countries that are more AI-ready tend to score considerably higher on global sustainability benchmarks — but the data suggest this reflects structural national differences (wealth, governance, infrastructure) rather than AI readiness directly improving sustainability scores year-on-year in the short run. For Fathima's thesis: **RQ1 confirms a strong positive association (r = 0.835) between AI preparedness and sustainability outcomes, consistent with the literature, though Fixed Effects models indicate the within-country, short-term causal channel remains to be demonstrated.**
