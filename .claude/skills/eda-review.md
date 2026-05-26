# /eda-review — EDA Plan Critical Review Agent

## Description
Reads one or all analysis plan files in `docs/2_plan/`, critically evaluates each section against statistical best-practice standards (panel data, small-N, moderation analysis, assumption validation, etc.), presents numbered issues and suggestions, then edits the plan files based on user-approved choices.

## Trigger
Invoked when the user runs `/eda-review` or `/eda-review <path>`, or asks to "review the EDA plan", "critique the analysis plan", "check the stats plan", or "improve the analysis plan".

## Arguments
- No argument → review every `.md` file in `docs/2_plan/`
- `<path>` → review only that file (relative or absolute)

---

## Instructions

Follow every step precisely in order. Do not skip steps. Do not make file edits until Step 6.

---

### Step 1 — Parse arguments and resolve files

1. Extract the optional `<path>` from the user's message or args string.
2. If a path is given:
   - Resolve it against the working directory.
   - Confirm the file ends in `.md`. If not, stop and tell the user.
   - Set `plan_files = [resolved_path]`
3. If no path is given:
   - Use `find docs/2_plan -name "*.md"` (via Bash) to list all plan files.
   - Sort them by filename.
   - Set `plan_files = [sorted list of paths]`
4. Tell the user which files you are about to review (one line per file).

---

### Step 2 — Load project context

Before reviewing, read the research proposal to anchor your critique in the study's actual goals and constraints:

- Read `docs/1_requirements/1_research_proposal.md`

Extract and hold in memory:
- Research questions (RQ1, RQ2, RQ3) and hypotheses (H1, H2, H3)
- Sample: 15 countries × 4 years = N=60 panel dataset
- Variables: `ai_readiness_score` (IV), `wgi_composite` (moderator), `sdg_index_score` (DV), `country_group` (Categorical)
- Study design: panel data, cross-country, 2020–2023
- Key constraints: small N, observational design, no randomisation

If the research proposal is not found, infer context from the plan files themselves and note the assumption.

---

### Step 3 — Read and parse each plan file

For each file in `plan_files`:
1. Read the full file.
2. Identify the plan's top-level purpose (RQ1, RQ2, RQ3, H1, H2, H3, or Data Gathering).
3. Split it into named sections based on `## Step N` headings.
4. Store as: `{ filename, purpose, sections: [{heading, body}] }`

---

### Step 4 — Critically evaluate each plan

For each parsed plan, apply the full checklist below. For every issue found, record:

```
{
  "plan": "filename",
  "section": "Step N heading",
  "issue_id": "P01" (P = plan code, 01 = sequential number),
  "severity": "Critical | Major | Minor",
  "issue": "One-sentence description of the problem",
  "why_it_matters": "One sentence on the consequence if ignored",
  "suggestion": "Specific, actionable fix written as a concrete plan step or addition"
}
```

#### Critical Evaluation Checklist

Apply every item below. Flag each gap or weakness found.

---

##### A. Small-N and Statistical Power

- [ ] Does the plan acknowledge that N=60 limits statistical power?
- [ ] Is there a power analysis or effect size discussion before choosing tests?
- [ ] Are any tests being used that require N > 100 (e.g., complex SEM, large-N bootstrap without qualification)?
- [ ] Are all per-subgroup analyses viable? (e.g., within-group regressions with only 5 countries per group may have too few degrees of freedom — flag if fewer than 10 obs per group)
- [ ] Does the plan report both statistical significance AND effect size (Cohen's d, η², partial R², etc.)?

##### B. Panel Data Assumptions

- [ ] Is cross-sectional dependence (Pesaran CD test) addressed before running FE/RE?
  - Countries sharing global AI/sustainability trends are likely spatially correlated — standard errors will be wrong without this check.
- [ ] Is serial autocorrelation (Wooldridge test for panel data) checked?
- [ ] Is heteroscedasticity tested (Breusch-Pagan or White test)?
- [ ] Are the standard errors clustered at the country level (not just at the observation level)?
- [ ] Is panel stationarity (Im-Pesaran-Shin or Levin-Lin-Chu unit root test) checked for continuous variables?
  - With only T=4, this is marginal but should be noted.
- [ ] Does the plan choose between FE and RE via a principled argument (not just the Hausman test alone)?
  - Hausman test is unreliable at N=15 countries; the plan should acknowledge this and supplement with economic reasoning.
- [ ] Is the between-effects (BE) estimator or pooled-mean group estimator considered as a robustness check?

##### C. Moderation / Interaction Analysis (Applies to H1, H2, H3 plans)

- [ ] Is the interaction term `ai_readiness_score × wgi_composite` explicitly included in the regression equation?
- [ ] Are the main effect terms (AI readiness, WGI) mean-centered before computing the interaction? (Reduces multicollinearity)
- [ ] Is multicollinearity between AI readiness and WGI checked (VIF or correlation matrix)?
  - Developed countries tend to score high on both — this is a structural risk.
- [ ] Is the Johnson-Neyman technique or simple slopes analysis planned to interpret the interaction at meaningful WGI levels?
- [ ] Does the plan distinguish moderation from mediation? (WGI could plausibly mediate too — worth ruling out)

##### D. Regression Model Specification

- [ ] Is model specification tested (RESET test or similar)?
- [ ] Are influential observations / leverage points identified (Cook's D, DFFITS)?
  - With N=60, one outlier country-year can dominate results.
- [ ] Are alternative functional forms tested (log-linear, quadratic) for the IV-DV relationship?
- [ ] Is the DV (SDG index) bounded 0–100 — should a fractional logit or beta regression be considered?
- [ ] Are the control variables justified? Is there a risk of overcontrolling (collider bias)?

##### E. Multiple Testing Correction

- [ ] The study tests RQ1, RQ2, RQ3 and H1, H2, H3 — is there a correction for multiple comparisons (Bonferroni, Benjamini-Hochberg)?
- [ ] Is the family-wise error rate discussed?

##### F. Visualisation Quality

- [ ] Does every key statistical claim have a corresponding visualisation planned?
- [ ] Are confidence intervals plotted (not just point estimates)?
- [ ] Are residual diagnostic plots (Q-Q plot, residuals vs fitted, scale-location) planned after each regression?
- [ ] Is the scatter plot coloured by country group? (Pattern may be driven entirely by the developed/developing split)

##### G. Reproducibility and Output Clarity

- [ ] Are all output file paths specified?
- [ ] Is the exact Python library and version noted for key tests (e.g., `linearmodels`, `statsmodels`)?
- [ ] Is there a step to save the full regression summary (not just coefficients) to a text file?
- [ ] Does the plan include a final interpretation step that links results back to the research question?

##### H. Data Plan Specific (applies to `01_data_gathering_plan.md`)

- [ ] Is there a data validation step that checks score ranges (SDG: 0–100, WGI: −2.5 to +2.5, AI Readiness: 0–100)?
- [ ] Is there a missingness audit? (What happens if a country-year is missing for any variable?)
- [ ] Is variable scale harmonisation planned before regression? (Standardisation or normalisation)
- [ ] Is there a correlation check between IV and moderator before merging (to pre-flag multicollinearity)?

---

### Step 5 — Present findings to the user

After evaluating all plans, present a structured review report in this format:

```
## EDA Plan Critical Review

Reviewed N plan file(s). Found X Critical, Y Major, Z Minor issues.

---

### [Plan filename] — [Plan purpose]

#### CRITICAL Issues

**[P01] Section: Step N — [Issue title]**
- **Problem:** [issue]
- **Why it matters:** [why_it_matters]
- **Suggested fix:** [suggestion]

#### MAJOR Issues

**[P02] Section: Step N — [Issue title]**
...

#### MINOR Issues
...

---

[Repeat for each plan file]

---

## Summary Table

| ID  | Plan | Section | Severity | Issue (short) |
|-----|------|---------|----------|----------------|
| P01 | ...  | ...     | Critical | ...            |
...

---

**Which issues would you like me to fix?**
Reply with:
- Issue IDs separated by commas (e.g. `P01, P03, P07`) to fix specific issues
- `all critical` to fix all Critical issues
- `all` to fix everything
- `none` to stop here
```

Wait for the user's reply before proceeding to Step 6.

---

### Step 6 — Apply user-approved fixes

After the user replies with their selection:

1. Parse the user's selection into a list of issue IDs.
2. Group the selected issues by target plan file.
3. For each plan file that has at least one selected issue:
   a. Read the current file content.
   b. For each selected issue targeting this file, apply the suggested fix:
      - **Additions**: Insert a new sub-step or note under the relevant `## Step N` section.
      - **Modifications**: Edit the existing step text to include the missing element.
      - **New steps**: Append a new `## Step N+1` section if the fix requires a wholly new step (renumber subsequent steps if needed).
   c. Write the updated file back using the Edit or Write tool.
   d. After each file is written, tell the user: "Updated `[filename]` — applied fixes: [list of IDs]."

**Formatting rules for edits:**
- Preserve the existing heading hierarchy and style.
- New steps use the same `## Step N — [Title]` format.
- New sub-bullets use `- ` list format matching the existing file.
- Never remove existing content unless it is directly contradicted by a fix — append or augment instead.
- Add a `> **Reviewer note (eda-review):**` prefix to any inserted text so the user can identify additions.

---

### Step 7 — Report completion

After all selected fixes are applied, output:

```
## Review Complete

Applied [N] fixes across [M] plan file(s).

Files modified:
- `docs/2_plan/XX_plan.md` — [N] fixes applied (IDs: ...)
- ...

Skipped (not selected):
- [List of IDs not applied, if any]

**Recommended next step:** Run `/eda-synthesis` after completing the EDA notebook to generate a CEO-readable summary of results.
```

If no fixes were applied (user selected `none`), say:
```
Review complete — no changes made. All issues have been documented above for your reference.
```
