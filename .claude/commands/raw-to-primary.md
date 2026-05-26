# /raw-to-primary — Raw Data Processing Pipeline

## Description
Processes every CSV file in `data/1_raw_data/` using **Polars** and writes a validated, tidy-format Parquet file per source into `data/2_primary_data/`. Follows data engineering best practices: schema-first ingestion, explicit type casting, wide→long reshaping, invariant validation, and compressed Parquet output. Creates the pipeline script at `pipelines/01_raw_to_primary.py` and a unit test stub at `test/test_01_raw_to_primary.py`.

## Trigger
Invoked when the user runs `/raw-to-primary`, or asks to "process raw data", "ingest raw files", "write primary data", "run the data pipeline", or "convert raw to parquet".

## Arguments
`/raw-to-primary [file]`

- No argument → process every `.csv` in `data/1_raw_data/`
- `[file]` → process only that specific file (relative or absolute path)

---

## Instructions

Follow every step in order. Do not write any files until Step 4.

---

### Step 1 — Discover raw files

1. If `[file]` is given, resolve it to an absolute path and set `raw_files = [that path]`.
2. Otherwise, run `find data/1_raw_data -name "*.csv"` via Bash and set `raw_files` to the sorted result.
3. If `raw_files` is empty, stop and tell the user: "No CSV files found in `data/1_raw_data/`."
4. Tell the user: "Found N file(s) to process: [list]."

---

### Step 2 — Inspect each raw file

For each file in `raw_files`, inspect it **before writing any code**:

1. Run a Bash snippet to print:
   - First 5 raw lines (to detect BOM, metadata header rows, footer rows, delimiter)
   - Total line count
   - File encoding (check for BOM: `\xef\xbb\xbf` = UTF-8 BOM, `\xff\xfe` = UTF-16 LE)
2. Use that output to determine the file's **quirks** and record them per file:

| Quirk | How to detect | What to record |
|-------|---------------|----------------|
| BOM present | First bytes are `\xef\xbb\xbf` | Set `encoding = "utf8-lossy"` |
| Metadata header rows | Row 0 is a label, not column names | Record `skip_rows = N` |
| Footer attribution rows | Last 1–3 rows are source text, not data | Record filter predicate to drop them |
| Non-standard delimiter | Not a comma | Record delimiter character |
| Wide format | Year or date strings as column names | Record `id_vars` and `value_vars` for unpivot |
| Multi-level headers | Two header rows merged | Record merge strategy |

3. From the column names (second header row if skip_rows > 0), classify each column:

| Column role | Identification | Target Polars dtype |
|-------------|----------------|---------------------|
| ISO / country code | 2–3 uppercase letters, ≤ 5 chars | `pl.Utf8` |
| Country name | Long string, not a number | `pl.Utf8` |
| Year | 4-digit integer string (e.g. `"2000"`) | `pl.Int16` |
| Score / metric | Decimal numeric string | `pl.Float32` |
| Integer count | Integer string | `pl.Int32` |
| Boolean flag | "yes"/"no", "true"/"false", 0/1 | `pl.Boolean` |
| Categorical | Low-cardinality string (< 30 unique) | `pl.Categorical` |

4. For the SDR-2025 overall-score file specifically, document:
   - Row 0: `"Overall score"` — section label, must be skipped (`skip_rows=1`)
   - Columns: `ISO`, `Country`, then year strings `"2000"` … `"2023"` (wide format)
   - Last row: attribution string starting with `"Sustainable Development Report"` — must be filtered out
   - Shape after cleaning: 27 countries × 24 years = 648 rows in long format
   - Output columns: `iso_code` (Utf8), `country` (Utf8), `year` (Int16), `sdr_score` (Float32)

---

### Step 3 — Define the coding standard

All code written in Step 4 **must** follow these rules exactly:

#### 3a. File structure

```
pipelines/01_raw_to_primary.py
├── Module docstring        — source path, output path, raw quirks handled
├── Imports block           — stdlib first, then polars, then src
├── Path constants          — ROOT, RAW_DIR, PRIMARY_DIR, per-file path variables
├── _validate(df) function  — assertion-based schema + invariant checks
├── _process_<stem>(path)   — one pure function per source file
├── run() function          — orchestrates all _process_* calls
└── if __name__ == "__main__" block — calls run(), prints shape + schema + head(10)
```

#### 3b. Polars ingestion rules

- Always read raw files with `infer_schema_length=0` to force all columns as `pl.Utf8` first — never let Polars auto-infer types from a dirty file.
- Pass `encoding="utf8-lossy"` when BOM or unknown encoding is detected.
- Use `skip_rows=N` (not `skiprows`) to skip metadata header lines.
- Never use `pd.read_csv` or any Pandas call. Polars only.

#### 3c. Wide-to-long (unpivot) rules

- Use `df.unpivot(on=value_cols, index=id_cols, variable_name=..., value_name=...)`.
- `id_cols` are the entity identifier columns (ISO, Country, etc.).
- `value_cols` are all remaining columns (year columns, score columns).
- Derive `value_cols` programmatically: `[c for c in df.columns if c not in id_cols]`.
- Never hardcode column lists — always derive from the schema at runtime so the pipeline handles schema drift.

#### 3d. Type casting rules

- Cast types **after** unpivoting, using `pl.col(...).cast(target_dtype)`.
- Cast year columns to `pl.Int16` (range 0–32767, sufficient for any year).
- Cast score/metric columns to `pl.Float32` (sufficient precision; saves ~50% vs Float64).
- Cast ISO / country string columns to `pl.Utf8` explicitly, even if already string.
- For Boolean columns: use `pl.col(c).str.to_lowercase().is_in(["true", "yes", "1"]).cast(pl.Boolean)`.
- Never use `.astype()` (that is Pandas API).

#### 3e. Filtering rules

- Drop footer/attribution rows with a `pl.filter()` predicate on a reliable key column.
  Example: `.filter(~pl.col("iso_code").str.starts_with("Sustainable"))`
- Drop fully-null rows: `.filter(pl.col(key_col).is_not_null() & (pl.col(key_col) != ""))`
- Apply all filters **before** type casting to avoid cast errors on junk rows.

#### 3f. Column naming rules

- All output column names must be `snake_case`.
- Use `.rename({...})` immediately after `unpivot()`.
- Forbidden column names: spaces, hyphens, parentheses, uppercase letters.
- Standard name mapping to document in the pipeline:
  - `"ISO"` → `"iso_code"`
  - `"Country"` → `"country"`
  - `variable_name` result → `"year"` (or the appropriate temporal key)
  - `value_name` result → meaningful metric name, e.g. `"sdr_score"`

#### 3g. Sort and deduplication rules

- Always sort by `[entity_key, temporal_key]` (e.g. `["iso_code", "year"]`) as the final transform step.
- After sort, assert no duplicates: `assert df.is_duplicated().sum() == 0`.

#### 3h. Validation function rules

The `_validate(df)` function must check all of the following and raise `AssertionError` or `ValueError` with a descriptive message on failure:

| Check | Code pattern |
|-------|-------------|
| Schema types match expected | `assert df.schema["col"] == pl.Xxx` for each column |
| No null values in any column | check `df.null_count()` row and assert all zeros |
| Expected year range present | `assert df["year"].unique().sort().to_list() == list(range(start, end+1))` |
| Expected row count | `assert df.shape[0] == expected_countries * expected_years` |
| Score column in valid range | `assert df["sdr_score"].min() >= 0.0 and df["sdr_score"].max() <= 100.0` |
| No duplicate (iso_code, year) pairs | `assert df.is_duplicated().sum() == 0` |

The `_validate` function must be called **before** writing to disk and must be idempotent (safe to call multiple times).

#### 3i. Parquet output rules

- Output directory: `data/2_primary_data/`
- One Parquet file per source CSV. Naming convention: `<source_stem_snake_case>.parquet`
  Example: `SDR-2025-overall-score (2).csv` → `sdr_2025_overall_score.parquet`
- Write with: `df.write_parquet(path, compression="snappy")`
- `snappy` compression is preferred: fast read/write, ~30–50% size reduction, widely supported.
- Never write CSV, JSON, or Feather as the output — Parquet only.
- Create the output directory with `PRIMARY_DIR.mkdir(parents=True, exist_ok=True)` inside `run()` before any writes.

#### 3j. Path handling rules

- All paths must be resolved relative to `ROOT = Path(__file__).resolve().parents[1]`.
- Never hardcode absolute paths. Never use `os.path` — use `pathlib.Path` throughout.
- File handles must never be left open — always read with Polars API (not `open()`).

#### 3k. Logging rules

- Use `print()` statements for pipeline progress (no `logging` module required for this task).
- Required print statements in `run()`:
  - Before each file: `Processing: <filename>`
  - After validation: `Validated: <N> rows × <M> cols | schema: {df.schema}`
  - After write: `Written → <output_path> (<file_size_kb> KB)`
- The `if __name__ == "__main__"` block must print `df.head(10)` so the output is inspectable at a glance.

#### 3l. Error handling rules

- Do **not** add try/except blocks that swallow errors silently.
- Let Polars exceptions propagate naturally — they are descriptive.
- Only catch exceptions to add context: wrap file-not-found with a message stating which file was expected.
- Never use bare `except:`.

---

### Step 4 — Write the pipeline file

Write `pipelines/01_raw_to_primary.py` using the Write tool, following the coding standard defined in Step 3 exactly. The file must:

1. Have a module docstring listing:
   - Source file(s)
   - Output file(s)
   - All raw file quirks being handled (one bullet per quirk, from Step 2)
2. Contain one `_process_<stem>` function per source file that:
   - Takes no arguments (paths are module-level constants)
   - Returns a `pl.DataFrame`
   - Contains inline comments only where a non-obvious choice is made (BOM skip, footer filter, etc.)
3. Contain a single `_validate(df)` function implementing all checks from §3h
4. Contain a `run()` function that calls each `_process_*` function, calls `_validate`, and writes the Parquet file
5. End with the `if __name__ == "__main__":` guard

---

### Step 5 — Write the test stub

Write `test/test_01_raw_to_primary.py` using the Write tool. The test file must:

1. Import the `run` function and the output path constant from the pipeline module.
2. Contain a `test_output_exists()` function that asserts the Parquet file exists after `run()` is called.
3. Contain a `test_schema()` function that reads the output Parquet with Polars and asserts the schema matches the expected schema.
4. Contain a `test_row_count()` function that asserts the expected number of rows.
5. Contain a `test_score_range()` function that asserts min and max of the score column are within valid bounds.
6. Contain a `test_no_nulls()` function that asserts zero null values across all columns.
7. Use `pytest` fixtures if test setup is shared.
8. Never use Pandas inside the test file — Polars only.

---

### Step 6 — Run the pipeline and verify

1. Run the pipeline via Bash: `python pipelines/01_raw_to_primary.py`
2. Capture stdout and stderr.
3. If the run fails, read the error, diagnose the root cause from the inspection data in Step 2, fix the pipeline file, and re-run.
4. Once the run succeeds, verify the output:
   - Run `python -c "import polars as pl; df = pl.read_parquet('data/2_primary_data/sdr_2025_overall_score.parquet'); print(df.shape, df.schema); print(df.head(10))"`
   - Confirm shape, schema, and sample rows match the expectations documented in Step 2.
5. Report the verified output to the user (shape, schema, file size).

---

### Step 7 — Run the tests

1. Run `python -m pytest test/test_01_raw_to_primary.py -v` via Bash.
2. If tests fail, fix the pipeline or tests and re-run.
3. Report the final test result to the user.

---

### Step 8 — Report completion

After all steps succeed, output:

```
## Raw → Primary Pipeline Complete

**Files processed:** N
**Output directory:** data/2_primary_data/

| Source file | Output file | Rows | Columns | Size |
|-------------|-------------|------|---------|------|
| <csv name>  | <parquet>   | NNN  | M       | XX KB|

**Pipeline:** `pipelines/01_raw_to_primary.py`
**Tests:** `test/test_01_raw_to_primary.py` — N passed

**Recommended next step:** Run `/dq-report data/2_primary_data/sdr_2025_overall_score.parquet` to audit the primary dataset before analysis.
```
