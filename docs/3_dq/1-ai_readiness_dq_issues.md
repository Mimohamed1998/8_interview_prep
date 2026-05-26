# Data Quality Report — Government AI Readiness Index (2020–2025)

**Source:** `data/1_raw_data/ai_readiness/ai_readiness_{year}.pdf`  
**Output:** `data/2_primary_data/ai_readiness/ai_readiness_2020_2025.{csv,parquet}`  
**Pipeline:** `pipelines/extract_ai_readiness.py`  
**Generated:** 2026-05-23

---

## Dataset Overview

| Year | Countries | total_score | government_pillar | technology_sector_pillar | data_infrastructure_pillar | 2025 pillars (6) |
|------|-----------|-------------|-------------------|--------------------------|---------------------------|------------------|
| 2020 | 172       | ✓           | NULL              | NULL                     | NULL                      | NULL             |
| 2021 | 160       | ✓           | ✓                 | ✓                        | ✓                         | NULL             |
| 2022 | 178       | ✓           | ✓                 | ✓                        | ✓                         | NULL             |
| 2023 | 193       | ✓           | ✓                 | ✓                        | ✓                         | NULL             |
| 2024 | 188       | ✓           | ✓                 | ✓                        | ✓                         | NULL             |
| 2025 | 195       | NULL        | NULL              | NULL                     | NULL                      | ✓                |

**Total rows extracted:** 1,086  
**Score range (2020–2024):** 9.20 – 88.16 (comparable across years, percent-point scale)

---

## DQ-001 · Missing Pillar Breakdown — 2020

**Severity:** Medium  
**Rows affected:** 172 (all 2020 rows)

The 2020 PDF (`Annex 1: Full Rankings`) publishes only a single composite score. The three sub-pillar columns — `government_pillar`, `technology_sector_pillar`, and `data_infrastructure_pillar` — were introduced starting with the 2021 edition. All 2020 rows carry `NULL` in those three columns.

**Impact:** 2020 data cannot be used in any analysis that compares pillar-level scores across years. Composite-score trend analysis (2020–2024) is unaffected.

---

## DQ-002 · Table Extraction Failure — 2022

**Severity:** Low (resolved via fallback)  
**Rows affected:** 0 in final output (fully recovered)

The 2022 PDF renders table borders as vector graphics; `pdfplumber`'s table extractor detects the header row on every page but returns zero data rows. Data was successfully recovered using raw text extraction and line-by-line regex parsing. Results were validated against the known score range and country count.

**Impact:** None on the final dataset. Future re-extraction or tooling changes should be tested against this file; do not rely on table-detection for 2022.

---

## DQ-003 · Squished Country Names (PDF Character-Encoding Artefact) — 2023 & 2024

**Severity:** High (auto-fixed)  
**Rows affected:** 44 names in 2023; 43 names in 2024

Both 2023 and 2024 PDFs lost spaces between words in multi-word country names during PDF creation. Examples of raw-extracted vs. corrected values:

| Raw (extracted) | Fixed |
|-----------------|-------|
| `UnitedStatesofAmerica` | `United States of America` |
| `RepublicofKorea` | `Republic of Korea` |
| `TrinidadandTobago` | `Trinidad and Tobago` |
| `LaoPeople'sDemocraticRepublic` | `Lao People's Democratic Republic` |
| `DemocraticRepublicoftheCongo` | `Democratic Republic of the Congo` |
| `SaintVincentandtheGrenadines` | `Saint Vincent and the Grenadines` |
| `Bolivia(PlurinationalStateof)` | `Bolivia(Plurinational State of)` |

**Fix applied:** Three-stage regex pipeline in `fix_squished_name()`:
1. Pre-split compound connectors: `andthe` → `and the`, `ofthe` → `of the`
2. Split connectors (`of`, `and`, `the`) directly before an uppercase letter
3. Split camelCase boundaries (lowercase → uppercase)
4. Split connectors directly before a space or closing parenthesis

**Residual risk:** The auto-fix cannot reliably repair all cases (see DQ-006 for remaining inconsistencies). Manual review is recommended before joining on the `country` column.

---

## DQ-004 · Missing Rank Column — 2024

**Severity:** Medium  
**Rows affected:** 188 (all 2024 rows)

The 2024 PDF presents countries in alphabetical order without a global rank column. Rank was inferred by sorting `total_score` descending and assigning a dense rank. Countries with identical scores receive the same rank.

**Impact:** 2024 `rank` values are derived, not directly sourced. They may differ from the official ranking if the publisher used a different tie-breaking method. Do not use 2024 ranks for precision rank-change comparisons without cross-checking against the official source.

---

## DQ-005 · Schema Change — New 6-Pillar Framework (2025)

**Severity:** High (by design, not an error)  
**Rows affected:** 195 (all 2025 rows)

The 2025 edition replaced the 3-pillar framework used in 2021–2024 with a new 6-pillar model. No composite `total_score` is published; only pillar-level scores are available.

| Old framework (2021–2024) | New framework (2025) |
|---------------------------|----------------------|
| `government_pillar`       | `policy_capacity` |
| `technology_sector_pillar`| `ai_infrastructure` |
| `data_infrastructure_pillar` | `governance` |
| *(no equivalent)*         | `public_sector_adoption` |
| *(no equivalent)*         | `development_diffusion` |
| *(no equivalent)*         | `resilience` |

**Impact:** 2025 rows carry `NULL` in all 2020–2024 columns and vice versa. The datasets are structurally incompatible for longitudinal analysis without constructing a crosswalk between the old and new frameworks.

---

## DQ-006 · Cross-Year Country Name Inconsistencies

**Severity:** Medium  
**Rows affected:** 18 distinct country name variants across years

After auto-fixing squished names (DQ-003), 18 country names still appear under different spellings across editions. These will cause silent row-duplication or misses in any cross-year join on the `country` column.

| Variants observed | Years | Root cause |
|-------------------|-------|------------|
| `Bolivia (Plurinational State of)` / `Bolivia(Plurinational State of)` | 2023–2025 | Space-before-paren inconsistency |
| `Côte D'Ivoire` / `Côted'Ivoire` | 2020, 2024 | 2024 squishing, apostrophe boundary |
| `Democratic People's Republic of Korea` | 2023, 2025 only | Not ranked in 2020–2022 editions |
| `Gambia (Republic of The)` / `Gambia(Republic of the)` | 2023–2025 | Paren format + case |
| `Iran (Islamic Republic of)` / `Iran(Islamic Republic of)` | 2023–2025 | Paren format |
| `Lao People's Democratic Republic` | 2020 only | Named differently in 2021–2024 as `Lao PDR` |
| `United Kingdom` / `United Kingdom of Great Britain and Northern Ireland` | multiple | Short vs. full official name |
| `Venezuela, Bolivarian Republic of` / `Venezuela,Bolivarian Republic of` | 2023–2025 | Comma-space formatting |
| `Micronesia (Federated States of)`, `Monaco`, `Nauru`, `Palau`, `Tuvalu` | 2023 & 2025 only | Coverage gap in 2020–2022 editions |

**Recommendation:** Create a canonical country name lookup table (`data/2_primary_data/country_name_map.csv`) mapping all variants to a single ISO 3166-1 alpha-3 code before performing cross-year joins.

---

## DQ-007 · Coverage Growth (Informational)

**Severity:** Informational  
**Note:** The number of ranked countries grew from 172 (2020) to 195 (2025), reflecting expansion of the index scope. Year-on-year comparisons should account for the fact that the 2021 dataset covers 160 countries (smallest coverage) while 2025 covers 195 (largest). Countries absent from earlier editions are not missing data — they were not included in those year's index.

---

## Summary Table

| ID | Issue | Year(s) | Severity | Status |
|----|-------|---------|----------|--------|
| DQ-001 | Missing pillar breakdown | 2020 | Medium | Documented — NULL columns |
| DQ-002 | Table extraction failure | 2022 | Low | Resolved — text fallback |
| DQ-003 | Squished country names | 2023, 2024 | High | Auto-fixed (44 + 43 names) |
| DQ-004 | Missing rank column | 2024 | Medium | Resolved — rank inferred from score |
| DQ-005 | Schema change (new pillars) | 2025 | High | Documented — NULL crosswalk |
| DQ-006 | Cross-year name variants | All | Medium | Documented — 18 variants remain |
| DQ-007 | Coverage growth | All | Info | Documented — expected |
