# /run-analysis — Analysis & Synthesis Agent

Reads a plan from `docs/2_plan/`, builds a complete Jupyter notebook under
`pipelines/eda_research_proposals/`, **executes it end-to-end**, validates all
outputs, then delivers McKinsey-style dark-navy charts and a plain-language
synthesis that any non-technical reader can follow.

**Usage:**
- `/run-analysis <plan>` — build, run, and validate a specific analysis plan

**`<plan>` accepts any of:**
- Plan number only: `02`, `03`, `04`, `05`, `06`, `07`
- Filename: `06_H2_plan.md`
- Full relative path: `docs/2_plan/06_H2_plan.md`

**Examples:**
```
/run-analysis 06                          # H2 — governance → sustainability
/run-analysis 02                          # RQ1 — AI readiness → SDG
/run-analysis docs/2_plan/03_RQ2_plan.md  # RQ2 — governance quality analysis
```

**What you get (automatically):**
- `pipelines/eda_research_proposals/<code>_analysis.ipynb` — executed notebook with embedded outputs
- `outputs/<code>_*.png` — McKinsey dark-navy charts (scatter, bar, line, heatmap, coefficient plot …)
- `outputs/<code>_*.csv` — regression results, descriptive stats, correlation tables
- `outputs/<code>_synthesis.md` — plain-language narrative Fathima can paste into her thesis
- Validation report confirming every cell ran clean and every expected file was produced

See `.claude/skills/run-analysis.md` for full agent instructions.
