# /eda-synthesis — EDA Executive Synthesis Generator

## Description
Reads a completed EDA Jupyter notebook, extracts all statistical outputs across every analysis section, and appends a final **Executive Synthesis** cell written for a non-technical CEO. Numbers are always grounded in the actual outputs — no placeholders, no invented figures. The tone is boardroom-ready: clear business language, decisive verdicts, and concrete "so what" implications.

## Trigger
Invoked when the user runs `/eda-synthesis` or asks to "summarise the EDA for the CEO", "write an executive synthesis", "explain the EDA results in plain English", or "add a CEO summary to the notebook".

## Arguments
`/eda-synthesis <notebook_path>`

- `<notebook_path>` — relative or absolute path to the `.ipynb` EDA notebook to synthesise.

---

## Instructions

Follow these steps precisely when this skill is invoked.

---

### Step 1 — Parse arguments

Extract `notebook_path` from the user's message or the args string.
- If relative, resolve against the current working directory.
- Always work with absolute paths internally.
- The file must end in `.ipynb`. If it does not, tell the user and stop.

---

### Step 2 — Read and parse the notebook

Use the Read tool to open the notebook at `notebook_path`. Parse it as JSON.

Extract the following from the cells array in order:
- All **markdown** cells: capture the source text (these are section headers and descriptions).
- All **code** cells: capture the source code AND the `outputs` array (stdout text_stream, execute_result, display_data).

Build a flat list called `sections`:
```
[
  { "type": "markdown" | "code", "source": "<full source text>", "output": "<concatenated stdout/text output>" },
  ...
]
```

For output extraction:
- `stream` outputs → join `text` array
- `execute_result` / `display_data` → join `data["text/plain"]` array if present
- Ignore image/png outputs

Concatenate all outputs for a code cell into one string.

---

### Step 3 — Extract statistical findings

Scan every `section` in `sections` and extract all numbers, rates, classifications, and conclusions. Build a structured `findings` dict by analysis domain. Use only values you can read directly from the text — never invent or estimate.

Extract the following domains (skip any that don't appear in the notebook):

#### A. Revenue & Concentration
- Total gross sales (dollar amount)
- Total number of SKUs
- Pareto segments: for each segment (Core / Growth / Long Tail) — number of SKUs and % of revenue
- Top SKU names and their revenue shares
- HHI at SKU, Product Line, and Brand level — and whether each is "high" or "moderate"

#### B. Growth & Strategic Positioning
- CAGR per product line
- Median CAGR across all product lines
- Strategic quadrant assignments: Protect & Invest / Defend / Nurture / Review/Exit — list the product lines in each
- Any single product line with notably positive or notably negative CAGR

#### C. Product Mix Dynamics
- Years covered
- Whether mix is stable or shifting (look for any commentary in markdown or obvious trend)

#### D. Return Risk
- Overall return rate (%)
- Return rate per category and brand
- Any categories flagged as elevated risk (z-score > 2)
- Chi-square test result: p-value and whether H₀ was rejected
- Practical implication stated in the notebook output

#### E. Demand Predictability
- Number and % of SKUs in each demand class: Continuous / Intermittent / Lumpy
- % of total volume represented by each class
- Recommended forecasting model per class

---

### Step 4 — Write the Executive Synthesis cell

Using every finding extracted in Step 3, compose a single richly-formatted **markdown** cell.

**Tone & style rules:**
- Write as a strategy consultant briefing a CEO — not a data scientist explaining code.
- Never use technical jargon without an immediate plain-English definition in parentheses.
- Every number must come from Step 3. Never round aggressively; use 1 decimal place for percentages.
- Use the word "you" or "your business" — make it personal and actionable.
- Each section must end with a **"So what"** sentence that states the business implication directly.
- No bullet lists longer than 5 items — force prioritisation.
- Bold the single most important number in each section.

**Structure the cell as follows:**

```markdown
---

## Executive Synthesis — What the Numbers Mean for the Business

> *Written for the CEO. Every figure is drawn directly from the data analysed above.*

---

### 1. How Concentrated Is Your Revenue? (Pareto & HHI)

[Plain-language paragraph explaining Pareto segments, top SKU dependence, and HHI scores.
 E.g.: "Your revenue is carried by a small group of products. The top 20 SKUs generate 79.6% of
 all gross sales, while 16 products in the 'Long Tail' together account for less than 6%.
 This is typical for FMCG portfolios — but it means a problem with any one of your top-5 SKUs
 would have an outsized impact on the entire business."
 Then state the HHI brand-level number and what it means practically.]

**So what:** [One-sentence verdict — e.g., "Your brand concentration is the biggest structural risk
 in the portfolio; a single brand disruption could cost you >85% of revenue."]

---

### 2. Are Your Products Growing or Declining? (CAGR & Strategic Matrix)

[Plain-language paragraph. Explain what CAGR means in one clause — "(the average annual growth
 rate over the study period)". State the median CAGR. Describe which product lines sit in each
 quadrant of the strategic matrix in plain terms — "your biggest earners are also your fastest
 declining" or "you have a few emerging lines worth nurturing".
 Call out the single highest-CAGR line and the single worst-declining line by name.]

**So what:** [One-sentence verdict — e.g., "With a median annual decline of -27%, the portfolio
 is contracting overall; your strategy should focus on protecting the Defend lines while
 accelerating the one breakout product (prod_line17) before the window closes."]

---

### 3. Is Your Product Mix Changing? (Mix Shift)

[Plain-language paragraph. Describe whether category and brand shares have shifted over the
 years covered. If one category is growing its share while others shrink, say so plainly.
 Relate this to the CAGR findings.]

**So what:** [One-sentence verdict on whether the mix shift is a risk or an opportunity.]

---

### 4. How Much Stock Is Being Returned — and Why Does It Matter? (Return Analysis)

[Plain-language paragraph. State the overall return rate. Explain: "For every 100 units shipped,
 roughly X come back." Rank the categories by return rate. Explain the chi-square result in one
 sentence — "Statistically, returns are not random — the category a product belongs to predicts
 how likely it is to be returned." State what this means for net revenue vs gross revenue.]

**So what:** [One-sentence verdict — e.g., "Category 2's 11.8% return rate is 30% above average;
 fixing the root cause here directly protects revenue without selling a single extra unit."]

---

### 5. How Predictable Is Demand? (Demand Continuity)

[Plain-language paragraph. Explain in simple terms what Continuous, Intermittent, and Lumpy
 mean: "Continuous means demand flows steadily every month — easy to forecast. Intermittent
 means demand shows up most months but with irregular spikes. Lumpy means demand is patchy
 and hard to predict." State the SKU counts and volume percentages for each class. Explain
 the forecasting model recommendation as a business outcome — not a model name.]

**So what:** [One-sentence verdict — e.g., "58% of your SKUs are intermittent, covering 70%
 of volume — this means your current stock replenishment model is likely both over-stocking
 slow months and under-stocking spike months simultaneously."]

---

### 6. The Three Things You Should Act On First

> Based on the full analysis, these are the highest-priority business decisions:

1. **[Action 1 — most urgent, derived from the biggest risk finding]**
   [2–3 sentences explaining what to do and why it matters in revenue or risk terms.]

2. **[Action 2 — second priority]**
   [2–3 sentences.]

3. **[Action 3 — third priority]**
   [2–3 sentences.]

---
*Analysis covers [N] SKUs, [N] product lines, [N] brands across [date range if available].
All figures are gross sales unless otherwise noted.*
```

Fill every bracket `[...]` with actual values from `findings`. Do not leave any placeholder unfilled.

---

### Step 5 — Inject the cell into the notebook

Open the notebook JSON (already read in Step 2). Append the new markdown cell to the end of the `cells` array:

```json
{
  "cell_type": "markdown",
  "id": "exec-synthesis-01",
  "metadata": {},
  "source": ["<line1>\n", "<line2>\n", "..."]
}
```

Split the markdown string into a list of lines where each line ends with `\n` except the last line.

Write the updated notebook JSON back to `notebook_path` using the Write tool (overwrite in place).

---

### Step 6 — Report to the user

After writing the file, tell the user:
- The notebook has been updated in place with an **Executive Synthesis** section at the end.
- Give a 4–6 bullet preview of the top findings surfaced in the synthesis (copy the "So what" sentences from each section).
- Remind them to open the notebook and scroll to the last cell, or run `Run All` to render it.
