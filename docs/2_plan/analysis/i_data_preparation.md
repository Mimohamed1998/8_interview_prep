# Plan d.i — Data Preparation

**Parent requirement:** [research_plan.md § d.i](../../1_requirements/research_plan.md)
**Depends on:** nothing (first step in the analysis pipeline)
**Feeds into:** [ii — Descriptive statistics and trend analysis](ii_descriptive_statistics_and_trend_analysis.md), [iii — Stationarity testing](iii_stationarity_testing.md), all downstream steps

## Objective

Produce one clean, regression-ready panel (the "analysis frame") covering 1990–2024, with
independently-recomputed PDI/MDI cross-checked against the pre-computed columns, the SHOCK
dummy constructed, and `log(FDI)` added as a documented deviation from the literal thesis
methodology. This is the single dataset every later step (ii–viii) reads from.

## Inputs
| File | Role |
|---|---|
| `data/processed/economic_indicators_yearly.csv` | Primary panel — `year, economic_resilience_index, product_diversification_index, market_diversification_index, inflation_rate_pct, fdi_net_inflows_usd, exchange_rate` (1990–2024, 35 rows). Cleaned equivalent of `Main_Data_Sheet.csv`. |
| `data/processed/economic_resilience_index.csv` | ERI construction detail — `year, gdp_growth_pct, unemployment_pct, trade_balance_pct_gdp, n_gdp, n_unemployment_inv, n_trade_balance_inv, eri` — used to verify `economic_resilience_index` in the main sheet. |
| `data/processed/product_diversification_exports_by_category.csv` | Export values (USD mn), wide format: 17 product categories as rows + a `Total Merchandise Exports` row, years 1986–2024 as columns. Source for independent PDI recomputation. |
| `data/processed/market_diversification_exports_by_country.csv` | Export values (USD), wide format: `year` + 21 destination-country columns + `total_exports`, 1990–2024. Source for independent MDI recomputation. |

## Method / Steps

1. **Load all four processed CSVs.** Confirm row counts and year ranges match what's documented
   above (35 rows for the main/market files, 1986–2024 span for the product file with categories
   as rows rather than columns — it needs transposing before use).

2. **Verify ERI independently.** Recompute `eri` from `economic_resilience_index.csv`'s
   normalized components (`n_gdp`, `n_unemployment_inv`, `n_trade_balance_inv`) — check the
   arithmetic (e.g., simple mean of the three) reproduces the `eri` column in that file, then
   confirm that file's `eri` matches `economic_indicators_yearly.csv`'s
   `economic_resilience_index` column year-for-year. Report any mismatch; do not silently pick
   one series over the other.

3. **Recompute PDI via HHI and cross-check.**
   - Transpose `product_diversification_exports_by_category.csv` so year is the row index and
     the 17 product categories are columns (drop the `Total Merchandise Exports` row — that is
     the denominator, not a share component).
   - Restrict to 1990–2024 (the product file starts in 1986; only 1990–2024 is in scope).
   - For each year, compute each category's export share `sᵢ = category_value / total_value`,
     using `Total Merchandise Exports` as the total. **Decision to flag:** confirm whether the
     sum of the 17 category values equals `Total Merchandise Exports` for every year — if not,
     note the residual and decide whether to treat it as an implicit "unclassified" share
     (which affects the HHI) or ignore it, and document the choice.
   - Compute `DIVP = 1 − Σsᵢ²` per year.
   - Compare the recomputed `DIVP` series against `product_diversification_index` in
     `economic_indicators_yearly.csv`. Report the discrepancy (e.g., mean absolute difference,
     max difference, and any year where the two disagree materially) rather than silently
     using one or the other.

4. **Recompute MDI via HHI and cross-check.**
   - From `market_diversification_exports_by_country.csv`, for each year compute each of the 21
     country columns' share of `total_exports`, i.e. `sᵢ = country_value / total_exports`.
   - **Decision to flag:** check whether `Σ(21 country columns)` equals `total_exports` for
     every year. The requirements doc describes "21 destination countries + Others/Total,"
     implying there may be an unlisted "Others" residual absorbed into `total_exports` but not
     broken out as its own column. If a residual exists, decide whether to add it as an
     "Others" share bucket in the HHI sum (recommended — omitting it overstates diversification)
     and document the choice.
   - Compute `DIVM = 1 − Σsᵢ²` per year.
   - Compare the recomputed `DIVM` series against `market_diversification_index` in
     `economic_indicators_yearly.csv`. Report the discrepancy the same way as for PDI.

5. **Construct the SHOCK dummy.** `SHOCK = 1` for years `{2008, 2009, 2020, 2021, 2022}`
   (per Ch. 3.3.3(d): global financial crisis + COVID-19/economic-crisis years), `SHOCK = 0`
   otherwise, for all 35 years.

6. **Log-transform FDI (flagged deviation).** Add `log_fdi = ln(fdi_net_inflows_usd)`. FDI
   ranges roughly $43M (1990) to $1.6B+ in later years against 0–1-bounded indices (ERI, PDI,
   MDI) — this scale mismatch motivates the log transform. This is **not** in the literal thesis
   spec (Ch. 3.5, Eq. 3.1 uses raw FDI), so state explicitly: *"FDI is log-transformed to reduce
   scale disparity with the bounded indices; the model using raw FDI is reported separately as a
   robustness check (see step viii)."* Confirm no zero/negative FDI values exist before taking
   the log (if any exist, flag — `ln` is undefined there).

7. **Assemble the final analysis frame.** One row per year, 1990–2024 (35 rows), columns:
   `year, eri, divp (recomputed), divm (recomputed), divp_source (precomputed, for reference),
   divm_source (precomputed, for reference), inflation_rate_pct, exchange_rate,
   fdi_net_inflows_usd, log_fdi, shock`. Keep both the recomputed and precomputed PDI/MDI columns
   side by side (don't overwrite) so the discrepancy from steps 3–4 remains visible/auditable
   downstream.

8. **Create the 1990–2023 subset (34 rows)** by dropping the 2024 row, held for the robustness
   check in step viii and for the explicit "extends the stated 1990–2023 period by one year"
   framing required in the write-up.

## Formulas

- HHI-based diversification index: `DIVᵢ = 1 − Σⱼ sᵢⱼ²`, where `sᵢⱼ` is category/country `j`'s
  share of the relevant total in year `i`. Bounded (0, 1); higher = more diversified.
- `log_fdi = ln(fdi_net_inflows_usd)`.

## Decisions & flags carried into this step (do not resolve silently)

- Whether the product/market export components sum exactly to their stated totals, and if not,
  how the residual is treated in the HHI recomputation (steps 3–4 above).
- Any ERI/PDI/MDI discrepancy between recomputed and precomputed values — report the numbers;
  do not pick a "winner" without surfacing it.
- Study period: 1990–2024 (35 obs) is the baseline; 1990–2023 (34 obs) is the robustness subset.
  This is already settled per the requirements doc — no judgment call needed here.
- Log(FDI) is an explicit, flagged deviation from the literal thesis spec; raw FDI is retained
  for the robustness check in step viii, not discarded.

## Outputs

- A saved analysis-ready CSV (e.g. `outputs/analysis_frame_1990_2024.csv`) and its 1990–2023
  subset (e.g. `outputs/analysis_frame_1990_2023.csv`).
- A short reconciliation note/table (ERI, PDI, MDI: recomputed vs. precomputed, by year) saved
  alongside, since this is the first thing an EViews cross-check would look at.

## Definition of done

- All four source files loaded and row counts verified.
- PDI and MDI independently recomputed via HHI and compared against precomputed columns, with
  discrepancies (if any) explicitly reported, not silently resolved.
- SHOCK dummy constructed for the correct 5 years.
- `log_fdi` added with the deviation explicitly justified in text.
- Two analysis frames saved (35-obs baseline, 34-obs robustness subset), ready for step ii.
