# Data Gathering Plan

**Study:** Does Governance Quality Moderate the Impact of AI Readiness on Sustainability Outcomes? A Cross-Country Analysis (2020–2023)

**Target Countries (15):**
- Developed: Finland, Denmark, Singapore, Germany, Japan
- Developing: India, Sri Lanka, Brazil, South Africa, Malaysia
- Lower governance: Nigeria, Bangladesh, Kenya, Pakistan, Ghana

**Target Years:** 2020, 2021, 2022, 2023
---

## Dataset 1: Sustainable Development Report (SDG Index Score)

**Status: ALREADY AVAILABLE — No download needed**

**File location:** `data/1_raw_data/SDR-2025-overall-score (2).csv`

**What it contains:**
- ISO country code, Country name
- SDG Overall Index Score per year (2000–2023)
- Covers all 15 target countries and all 4 target years (2020–2023)

**Action required:**
1. Filter the existing CSV for the 15 target countries using ISO codes:
   - FIN, DNK, SGP, DEU, JPN, IND, LKA, BRA, ZAF, MYS, NGA, BGD, KEN, PAK, GHA
2. Extract columns for years: 2020, 2021, 2022, 2023
3. Reshape from wide to long format (one row per country-year)
4. Save to `data/2_processed_data/sdg_index_2020_2023.csv`

**No internet access or API key required.**

---- 

## Dataset 2: World Governance Indicators (WGI)

**Source:** World Bank — Worldwide Governance Indicators
**Reliability:** Official World Bank dataset, globally authoritative

**Direct download URL:**
> https://www.worldbank.org/en/publication/worldwide-governance-indicators/interactive-data-access

**What to collect:**
- Six WGI dimensions for each country-year (2020–2023):
  1. Voice and Accountability (VA)
  2. Political Stability and Absence of Violence (PV)
  3. Government Effectiveness (GE)
  4. Regulatory Quality (RQ)
  5. Rule of Law (RL)
  6. Control of Corruption (CC)
- Composite WGI average score = mean of the six dimensions (this is the moderator variable)

---

### Option A — Agent can do this directly (Recommended)

**Method: World Bank API via `wbgapi` Python package**

- No API key required
- `wbgapi` is a free, open-access Python library for World Bank data
- WGI indicators are available under the `wgi` source (source ID: 3)

**WGI Indicator codes:**
| Indicator | Code |
|-----------|------|
| Voice and Accountability | WGI.VA.EST |
| Political Stability | WGI.PV.EST |
| Government Effectiveness | WGI.GE.EST |
| Regulatory Quality | WGI.RQ.EST |
| Rule of Law | WGI.RL.EST |
| Control of Corruption | WGI.CC.EST |

**Steps for agent:**
1. Install `wbgapi`: `pip install wbgapi`
2. Query the 6 WGI indicators for the 15 target countries and years 2020–2023
3. Compute composite WGI score as the mean of the 6 dimensions per country-year
4. Save to `data/2_processed_data/wgi_2020_2023.csv`

---

### Option B — Manual download (Fallback if API fails)

1. Go to: https://info.worldbank.org/governance/wgi/
2. Click "Download Data" → Download the full Excel file `WGI_Data.xlsx`
3. Open the Excel file, navigate to the "Data" tab
4. Filter rows: `Indicator` is one of the 6 WGI codes above
5. Filter columns: Country ISO codes for the 15 target countries
6. Extract values for years 2020–2023
7. Compute average WGI score per country-year
8. Save to `data/2_processed_data/wgi_2020_2023.csv`

---

## Dataset 3: AI Readiness Index (AIRI)

**Source:** Oxford Insights — Government AI Readiness Index
**Reliability:** Oxford Insights is the canonical source for the Government AI Readiness Index, widely cited in academic literature including the research references

**Direct download URL:**
> https://oxfordinsights.com/ai-readiness/aireadiness/

**What to collect:**
- Overall AI Readiness Index score per country per year (2020–2023)
- Published annually; separate reports for 2020, 2021, 2022, 2023

---

### Option A — Manual download (YOU must do this)

Oxford Insights does not provide a public API. The data is released as annual PDF reports with accompanying Excel/CSV data files.

**Steps you need to do manually:**
1. Go to: https://oxfordinsights.com/ai-readiness/aireadiness/
2. For each year (2020, 2021, 2022, 2023), locate and download the data file:
   - Look for "Download Data" or "Excel" buttons on the page
   - Alternatively, search for "Oxford Insights AI Readiness Index [year] data download"
3. From each year's file, extract the overall AI Readiness Index score for the 15 target countries
4. Compile into a single file with columns: `country`, `iso_code`, `year`, `ai_readiness_score`
5. Save to `data/2_processed_data/ai_readiness_2020_2023.csv`

**Note on data availability:**
- The 2020 index covers 172 countries
- The 2021, 2022, 2023 indexes are also available on the Oxford Insights website
- Verify that all 15 target countries appear in each year's dataset

---

### Option B — Alternative academic mirror (If Oxford Insights download fails)

The Oxford Insights AI Readiness data is sometimes hosted in supplementary materials on:
- Harvard Dataverse: https://dataverse.harvard.edu (search "Oxford Insights AI Readiness")
- The NESTA portal or similar open-data repositories

---

## Final Merged Dataset

Once all three datasets are collected and processed:

| Column | Source | Type |
|--------|--------|------|
| `iso_code` | All | String |
| `country` | All | String |
| `year` | All | Integer (2020–2023) |
| `ai_readiness_score` | Oxford Insights AIRI | Float (Independent Variable) |
| `wgi_composite` | World Bank WGI | Float (Moderator Variable) |
| `sdg_index_score` | SDR | Float (Dependent Variable) |
| `country_group` | Assigned | Categorical (Developed/Developing/Lower Governance) |

**Merge steps:**
1. Merge SDG data + WGI data on `iso_code` and `year`
2. Merge result + AI Readiness data on `iso_code` and `year`
3. Verify no missing values for target country-years
4. Add `country_group` column based on research proposal classification
5. Save final dataset to `data/2_processed_data/panel_dataset_2020_2023.csv`

**Expected shape:** 60 rows (15 countries × 4 years), 7 columns

---

## Data Quality Checks Before Analysis

- Confirm all 15 countries × 4 years = 60 rows are present (no gaps)
- Verify score ranges are plausible:
  - SDG Index: typically 0–100
  - WGI composite: typically −2.5 to +2.5 (or normalized 0–100 if using percentile rank)
  - AI Readiness: typically 0–100
- Check for extreme outliers (flag, do not remove without justification)
- Standardize variable scales if needed before regression (z-score normalization)
