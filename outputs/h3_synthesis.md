## 📊 Plain-Language Synthesis
> *Written for readers who are not statisticians*

---

### What did we study?

This analysis tested whether governance quality acts as a multiplier for the benefit that AI technology brings to a country's sustainability performance. Using data from 26 countries between 2020 and 2023, we asked: does the same level of AI readiness "work better" in countries that are governed well? Think of it like asking whether good soil (governance) makes seeds (AI readiness) grow faster into food (sustainability outcomes). H3 predicted that the answer is yes — higher governance would amplify AI's sustainability dividend.

---

### What did we find?

#### Finding 1 — Governance Does Not Amplify the AI-Sustainability Link
The interaction coefficient β3 = −0.034 (RE model), with a one-tailed p-value of 0.957, far above the 0.05 threshold. H3 is not supported. Contrary to expectations, governance quality does not positively moderate the AI → SDG relationship in this sample. In practical terms, a 10-point increase in AI readiness translates to 0.77 additional SDG points in low-governance countries but only 0.07 points in high-governance countries — the *opposite* of what H3 predicted.

#### Finding 2 — AI Readiness Has Its Strongest Marginal Effect Where Governance Is Weakest
Simple slopes analysis reveals that the conditional effect of AI readiness on SDG scores is 0.0774 in low-governance contexts (WGI = mean − 1 SD ≈ −0.67), 0.0422 at mean governance, and just 0.0070 in high-governance contexts (WGI = mean + 1 SD ≈ 1.38). This pattern likely reflects a ceiling effect: countries with strong governance already score highly on SDG outcomes through that governance, leaving little additional room for AI readiness to add value. In lower-governance settings, AI readiness serves as a partial substitute for institutional capacity.

#### Finding 3 — Uncertainty Is High; Bootstrap CI Spans Zero
A 1,000-sample cluster-bootstrap procedure produced a 95% CI for β3 of [−0.332, +0.016], which includes zero. Across all four individual years (2020–2023), β3 is consistently negative (ranging from −0.10 to −0.22) — which further argues against positive moderation. The Pooled OLS floodlight analysis indicates that AI Readiness has a statistically significant (p < 0.05) effect on SDG only for countries with WGI ≤ approximately 0.21 — that is, for lower-to-middle governance performers.

---

### How confident are we?

| What we measured | Result | Confidence |
|-----------------|--------|------------|
| Interaction effect β3 (H3 test) | −0.034 (RE); p one-tail = 0.957 | ❌ Not significant — H3 not supported |
| Bootstrap 95% CI for β3 | [−0.332, +0.016] | Includes zero — high uncertainty |
| Year-by-year consistency | β3 negative in all 4 years | Consistent direction, but not statistically significant |
| Effect size (model R²) | 0.259 (RE model) | Moderate — model explains ~26% of within-country variation |
| Governance main effect β2 | +3.03 (RE), p < 0.001 | Strong direct effect of governance on SDG ✅ |

> **Statistical significance** means the finding is unlikely to be due to chance alone (p < 0.05).
> **One-tailed test** is stricter here because H3 specifically predicts a *positive* interaction; a negative β3 immediately fails H3 regardless of magnitude.

---

### What are the limitations?

- **Sample size:** With 104 observations across 26 countries, statistical power for detecting small interaction effects is low. Cohen's f² ≈ 0.35 for the full model is medium-to-large, but specifically for the interaction term, the power is limited.
- **Time span:** Four years (2020–2023) is a short window; longitudinal moderation effects may require a decade or more to materialise.
- **Observational data:** We cannot establish causation. Both AI readiness and governance quality are correlated with national income and institutional history, which may confound the moderation.
- **Ceiling effect in high-governance countries:** Countries like Finland, Denmark, and Norway score near the top of both governance and SDG scales; this compression limits statistical detectability of any further amplification.
- **Hausman test degeneracy:** With a small panel, the Hausman test produced a degenerate result (negative chi-squared), indicating both FE and RE are plausible. Results should be interpreted cautiously.

---

### In plain English: Governance quality does not amplify AI's sustainability benefits in this sample — if anything, AI readiness matters most where governance is weakest, suggesting it acts as a partial institutional substitute rather than a complement.
