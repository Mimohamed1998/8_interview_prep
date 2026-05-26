"""
Raw → Primary pipeline for SDR and WGI datasets.

Sources:
  data/1_raw_data/SDR-2025-overall-score (2).csv
  data/1_raw_data/wgi_2020_2024.csv

Outputs:
  data/2_primary_data/sdr_2025_overall_score.parquet
  data/2_primary_data/wgi_2020_2024.parquet

SDR quirks handled:
  - UTF-8 BOM present → encoding="utf8-lossy"
  - Row 0 is "Overall score" section label → skip_rows=1
  - Wide format: year columns 2000–2023 → unpivot to long
  - Last row is attribution text → filtered by iso_code prefix check
  - Expected shape: 26 countries × 24 years = 624 rows

WGI quirks handled:
  - Already tidy long format → no unpivot needed
  - Column names VA, PV, GE, RQ, RL, CC are uppercase → renamed to lowercase
  - WGI composite scores range ≈ −2.5 to 2.5 (not 0–100)
  - Expected shape: 26 countries × 5 years (2020–2024) = 130 rows
"""

from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "1_raw_data"
PRIMARY_DIR = ROOT / "data" / "2_primary_data"

SDR_RAW = RAW_DIR / "SDR-2025-overall-score (2).csv"
WGI_RAW = RAW_DIR / "wgi_2020_2024.csv"

SDR_OUT = PRIMARY_DIR / "sdr_2025_overall_score.parquet"
WGI_OUT = PRIMARY_DIR / "wgi_2020_2024.parquet"

SDR_EXPECTED_COUNTRIES = 26
SDR_EXPECTED_YEARS = 24   # 2000–2023
SDR_YEAR_START = 2000
SDR_YEAR_END = 2023

WGI_EXPECTED_COUNTRIES = 26
WGI_EXPECTED_YEARS = 5    # 2020–2024
WGI_YEAR_START = 2020
WGI_YEAR_END = 2024


def _validate_sdr(df: pl.DataFrame) -> None:
    assert df.schema["iso_code"] == pl.Utf8, "iso_code must be Utf8"
    assert df.schema["country"] == pl.Utf8, "country must be Utf8"
    assert df.schema["year"] == pl.Int16, "year must be Int16"
    assert df.schema["sdr_score"] == pl.Float32, "sdr_score must be Float32"

    null_counts = df.null_count()
    for col in df.columns:
        n = null_counts[col][0]
        assert n == 0, f"Null values found in SDR column '{col}': {n}"

    expected_years = list(range(SDR_YEAR_START, SDR_YEAR_END + 1))
    actual_years = df["year"].unique().sort().to_list()
    assert actual_years == expected_years, f"SDR year mismatch: {actual_years}"

    expected_rows = SDR_EXPECTED_COUNTRIES * SDR_EXPECTED_YEARS
    assert df.shape[0] == expected_rows, (
        f"SDR row count mismatch: expected {expected_rows}, got {df.shape[0]}"
    )

    assert df["sdr_score"].min() >= 0.0, "sdr_score below 0"
    assert df["sdr_score"].max() <= 100.0, "sdr_score above 100"

    assert df.is_duplicated().sum() == 0, "Duplicate (iso_code, year) pairs in SDR"


def _validate_wgi(df: pl.DataFrame) -> None:
    expected_cols = {
        "iso_code": pl.Utf8,
        "country": pl.Utf8,
        "year": pl.Int16,
        "va": pl.Float32,
        "pv": pl.Float32,
        "ge": pl.Float32,
        "rq": pl.Float32,
        "rl": pl.Float32,
        "cc": pl.Float32,
        "wgi_composite": pl.Float32,
    }
    for col, dtype in expected_cols.items():
        assert df.schema[col] == dtype, f"WGI column '{col}' must be {dtype}"

    null_counts = df.null_count()
    for col in df.columns:
        n = null_counts[col][0]
        assert n == 0, f"Null values found in WGI column '{col}': {n}"

    expected_years = list(range(WGI_YEAR_START, WGI_YEAR_END + 1))
    actual_years = df["year"].unique().sort().to_list()
    assert actual_years == expected_years, f"WGI year mismatch: {actual_years}"

    expected_rows = WGI_EXPECTED_COUNTRIES * WGI_EXPECTED_YEARS
    assert df.shape[0] == expected_rows, (
        f"WGI row count mismatch: expected {expected_rows}, got {df.shape[0]}"
    )

    # WGI governance scores are bounded by −2.5 to 2.5
    for col in ["va", "pv", "ge", "rq", "rl", "cc", "wgi_composite"]:
        assert df[col].min() >= -2.5, f"{col} below −2.5"
        assert df[col].max() <= 2.5, f"{col} above 2.5"

    assert df.is_duplicated().sum() == 0, "Duplicate (iso_code, year) pairs in WGI"


def _process_sdr() -> pl.DataFrame:
    # BOM present → utf8-lossy; skip_rows=1 skips the "Overall score" section label
    df = pl.read_csv(
        SDR_RAW,
        infer_schema_length=0,
        encoding="utf8-lossy",
        skip_rows=1,
    )

    id_cols = ["ISO", "Country"]
    value_cols = [c for c in df.columns if c not in id_cols]

    # Filter attribution footer before any type casting to avoid cast errors
    df = df.filter(
        pl.col("ISO").is_not_null()
        & (pl.col("ISO") != "")
        & ~pl.col("ISO").str.starts_with("Sustainable")
    )

    df = (
        df.unpivot(on=value_cols, index=id_cols, variable_name="year", value_name="sdr_score")
        .rename({"ISO": "iso_code", "Country": "country"})
        .with_columns([
            pl.col("iso_code").cast(pl.Utf8),
            pl.col("country").cast(pl.Utf8),
            pl.col("year").cast(pl.Int16),
            pl.col("sdr_score").cast(pl.Float32),
        ])
        .sort(["iso_code", "year"])
    )

    return df


def _process_wgi() -> pl.DataFrame:
    df = pl.read_csv(WGI_RAW, infer_schema_length=0)

    df = df.filter(
        pl.col("iso_code").is_not_null() & (pl.col("iso_code") != "")
    )

    df = (
        df.rename({
            "VA": "va",
            "PV": "pv",
            "GE": "ge",
            "RQ": "rq",
            "RL": "rl",
            "CC": "cc",
        })
        .with_columns([
            pl.col("iso_code").cast(pl.Utf8),
            pl.col("country").cast(pl.Utf8),
            pl.col("year").cast(pl.Int16),
            pl.col("va").cast(pl.Float32),
            pl.col("pv").cast(pl.Float32),
            pl.col("ge").cast(pl.Float32),
            pl.col("rq").cast(pl.Float32),
            pl.col("rl").cast(pl.Float32),
            pl.col("cc").cast(pl.Float32),
            pl.col("wgi_composite").cast(pl.Float32),
        ])
        .sort(["iso_code", "year"])
    )

    return df


def run() -> tuple[pl.DataFrame, pl.DataFrame]:
    PRIMARY_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Processing: {SDR_RAW.name}")
    sdr = _process_sdr()
    _validate_sdr(sdr)
    print(f"Validated: {sdr.shape[0]} rows × {sdr.shape[1]} cols | schema: {sdr.schema}")
    sdr.write_parquet(SDR_OUT, compression="snappy")
    size_kb = SDR_OUT.stat().st_size // 1024
    print(f"Written → {SDR_OUT} ({size_kb} KB)")

    print(f"Processing: {WGI_RAW.name}")
    wgi = _process_wgi()
    _validate_wgi(wgi)
    print(f"Validated: {wgi.shape[0]} rows × {wgi.shape[1]} cols | schema: {wgi.schema}")
    wgi.write_parquet(WGI_OUT, compression="snappy")
    size_kb = WGI_OUT.stat().st_size // 1024
    print(f"Written → {WGI_OUT} ({size_kb} KB)")

    return sdr, wgi


if __name__ == "__main__":
    sdr_df, wgi_df = run()
    print("\n--- SDR head(10) ---")
    print(sdr_df.head(10))
    print("\n--- WGI head(10) ---")
    print(wgi_df.head(10))
