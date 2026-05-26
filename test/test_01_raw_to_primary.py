import importlib
import sys
from pathlib import Path

import polars as pl
import pytest

# Python identifiers can't start with digits; use importlib for this module.
_mod = importlib.import_module("pipelines.01_raw_to_primary")

run = _mod.run
SDR_OUT = _mod.SDR_OUT
WGI_OUT = _mod.WGI_OUT
SDR_EXPECTED_COUNTRIES = _mod.SDR_EXPECTED_COUNTRIES
SDR_EXPECTED_YEARS = _mod.SDR_EXPECTED_YEARS
SDR_YEAR_START = _mod.SDR_YEAR_START
SDR_YEAR_END = _mod.SDR_YEAR_END
WGI_EXPECTED_COUNTRIES = _mod.WGI_EXPECTED_COUNTRIES
WGI_EXPECTED_YEARS = _mod.WGI_EXPECTED_YEARS
WGI_YEAR_START = _mod.WGI_YEAR_START
WGI_YEAR_END = _mod.WGI_YEAR_END


@pytest.fixture(scope="module")
def outputs():
    return run()


@pytest.fixture(scope="module")
def sdr_df(outputs):
    return outputs[0]


@pytest.fixture(scope="module")
def wgi_df(outputs):
    return outputs[1]


# --- SDR tests ---

def test_sdr_output_exists():
    assert SDR_OUT.exists(), f"SDR parquet not found at {SDR_OUT}"


def test_sdr_schema(sdr_df):
    assert sdr_df.schema["iso_code"] == pl.Utf8
    assert sdr_df.schema["country"] == pl.Utf8
    assert sdr_df.schema["year"] == pl.Int16
    assert sdr_df.schema["sdr_score"] == pl.Float32


def test_sdr_row_count(sdr_df):
    expected = SDR_EXPECTED_COUNTRIES * SDR_EXPECTED_YEARS
    assert sdr_df.shape[0] == expected, f"Expected {expected} rows, got {sdr_df.shape[0]}"


def test_sdr_score_range(sdr_df):
    assert sdr_df["sdr_score"].min() >= 0.0
    assert sdr_df["sdr_score"].max() <= 100.0


def test_sdr_no_nulls(sdr_df):
    null_counts = sdr_df.null_count()
    for col in sdr_df.columns:
        assert null_counts[col][0] == 0, f"Nulls in SDR column '{col}'"


def test_sdr_year_range(sdr_df):
    expected = list(range(SDR_YEAR_START, SDR_YEAR_END + 1))
    actual = sdr_df["year"].unique().sort().to_list()
    assert actual == expected


def test_sdr_no_duplicates(sdr_df):
    assert sdr_df.is_duplicated().sum() == 0


# --- WGI tests ---

def test_wgi_output_exists():
    assert WGI_OUT.exists(), f"WGI parquet not found at {WGI_OUT}"


def test_wgi_schema(wgi_df):
    expected = {
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
    for col, dtype in expected.items():
        assert wgi_df.schema[col] == dtype, f"WGI column '{col}' expected {dtype}"


def test_wgi_row_count(wgi_df):
    expected = WGI_EXPECTED_COUNTRIES * WGI_EXPECTED_YEARS
    assert wgi_df.shape[0] == expected, f"Expected {expected} rows, got {wgi_df.shape[0]}"


def test_wgi_score_range(wgi_df):
    for col in ["va", "pv", "ge", "rq", "rl", "cc", "wgi_composite"]:
        assert wgi_df[col].min() >= -2.5, f"{col} below −2.5"
        assert wgi_df[col].max() <= 2.5, f"{col} above 2.5"


def test_wgi_no_nulls(wgi_df):
    null_counts = wgi_df.null_count()
    for col in wgi_df.columns:
        assert null_counts[col][0] == 0, f"Nulls in WGI column '{col}'"


def test_wgi_year_range(wgi_df):
    expected = list(range(WGI_YEAR_START, WGI_YEAR_END + 1))
    actual = wgi_df["year"].unique().sort().to_list()
    assert actual == expected


def test_wgi_no_duplicates(wgi_df):
    assert wgi_df.is_duplicated().sum() == 0
