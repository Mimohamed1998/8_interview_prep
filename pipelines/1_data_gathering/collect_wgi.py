"""
Collects World Governance Indicators (WGI) from the World Bank REST API
for 26 target countries across 2020-2023.

Uses direct HTTP requests to the World Bank v2 API — no API key required.

Output: data/1_raw_data/wgi_2020_2023.csv
Columns: iso_code, country, year, VA, PV, GE, RQ, RL, CC, wgi_composite
"""

import sys
from pathlib import Path

import pandas as pd
import requests

# --- Constants -----------------------------------------------------------

COUNTRY_NAMES = {
    "BGD": "Bangladesh",
    "BRA": "Brazil",
    "CAN": "Canada",
    "CHN": "China",
    "DNK": "Denmark",
    "ETH": "Ethiopia",
    "FIN": "Finland",
    "DEU": "Germany",
    "GHA": "Ghana",
    "IND": "India",
    "IDN": "Indonesia",
    "JPN": "Japan",
    "KEN": "Kenya",
    "MYS": "Malaysia",
    "MEX": "Mexico",
    "NLD": "Netherlands",
    "NGA": "Nigeria",
    "NOR": "Norway",
    "PAK": "Pakistan",
    "SGP": "Singapore",
    "ZAF": "South Africa",
    "LKA": "Sri Lanka",
    "SWE": "Sweden",
    "THA": "Thailand",
    "USA": "United States",
    "VNM": "Vietnam",
}

TARGET_COUNTRIES = list(COUNTRY_NAMES.keys())
TARGET_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]

# World Bank source 3 (WGI) indicator codes — estimate values on -2.5 to +2.5 scale
WGI_INDICATORS = {
    "GOV_WGI_GE.EST": "GE",   # Government Effectiveness
    "GOV_WGI_VA.EST": "VA",   # Voice and Accountability
    "GOV_WGI_PV.EST": "PV",   # Political Stability and Absence of Violence
    "GOV_WGI_RQ.EST": "RQ",   # Regulatory Quality
    "GOV_WGI_RL.EST": "RL",   # Rule of Law
    "GOV_WGI_CC.EST": "CC",   # Control of Corruption
}

WB_SOURCE3_URL = (
    "https://api.worldbank.org/v2/en/sources/3"
    "/series/{series}/country/{countries}/time/{time}"
)

OUTPUT_PATH = Path(__file__).parents[2] / "data" / "1_raw_data" / "wgi_2020_2024.csv"


# --- Fetch ---------------------------------------------------------------

def _parse_source3_response(payload: dict) -> list[dict]:
    """Parse the nested source-3 API response into flat row dicts."""
    data = payload.get("source", {}).get("data", [])
    rows = []
    for entry in data:
        if entry.get("value") is None:
            continue
        vars_ = {v["concept"]: v["id"] for v in entry.get("variable", [])}
        rows.append({
            "series_id": vars_.get("Series"),
            "iso_code": vars_.get("Country"),
            "year": int(vars_["Time"].replace("YR", "")),
            "value": float(entry["value"]),
        })
    return rows


def fetch_all_wgi() -> pd.DataFrame:
    series_str = ";".join(WGI_INDICATORS.keys())
    countries_str = ";".join(TARGET_COUNTRIES)
    time_str = ";".join(f"YR{y}" for y in TARGET_YEARS)

    url = WB_SOURCE3_URL.format(
        series=series_str,
        countries=countries_str,
        time=time_str,
    )
    print(f"  Querying World Bank source 3 for all 6 indicators...", end=" ", flush=True)

    response = requests.get(url, params={"format": "json", "per_page": 2000}, timeout=30)
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, dict) or "source" not in payload:
        raise ValueError(f"Unexpected API response structure: {str(payload)[:200]}")

    rows = _parse_source3_response(payload)
    print(f"{len(rows)} records fetched")

    df = pd.DataFrame(rows)

    # Pivot so each WGI indicator becomes a column
    short_name_map = WGI_INDICATORS
    df["indicator"] = df["series_id"].map(short_name_map)
    df = df.pivot_table(
        index=["iso_code", "year"],
        columns="indicator",
        values="value",
        aggfunc="first",
    ).reset_index()
    df.columns.name = None

    return df


# --- Compute and validate ------------------------------------------------

def compute_composite(df: pd.DataFrame) -> pd.DataFrame:
    dim_cols = [c for c in ["VA", "PV", "GE", "RQ", "RL", "CC"] if c in df.columns]
    df["wgi_composite"] = df[dim_cols].mean(axis=1)
    df.insert(1, "country", df["iso_code"].map(COUNTRY_NAMES))
    return df


def validate(df: pd.DataFrame) -> None:
    expected = len(TARGET_COUNTRIES) * len(TARGET_YEARS)
    print(f"\nValidation:")
    print(f"  Expected rows : {expected}  ({len(TARGET_COUNTRIES)} countries × {len(TARGET_YEARS)} years)")
    print(f"  Actual rows   : {len(df)}")

    present = set(zip(df["iso_code"], df["year"]))
    missing = [(iso, yr) for iso in TARGET_COUNTRIES for yr in TARGET_YEARS if (iso, yr) not in present]
    if missing:
        print(f"  Missing country-years: {missing}")

    dim_cols = [c for c in ["VA", "PV", "GE", "RQ", "RL", "CC", "wgi_composite"] if c in df.columns]
    missing_vals = df[dim_cols].isna().sum()
    if missing_vals.any():
        print(f"  Missing values per column:\n{missing_vals[missing_vals > 0].to_string()}")
    else:
        print(f"  No missing values in dimension columns")

    lo, hi = df["wgi_composite"].min(), df["wgi_composite"].max()
    print(f"  wgi_composite range: {lo:.3f} to {hi:.3f}  (expected ≈ -2.5 to +2.5)")


# --- Main ----------------------------------------------------------------

def main() -> None:
    print("Fetching WGI data from World Bank API...")
    df = fetch_all_wgi()
    df = compute_composite(df)

    col_order = ["iso_code", "country", "year", "VA", "PV", "GE", "RQ", "RL", "CC", "wgi_composite"]
    col_order = [c for c in col_order if c in df.columns]
    df = df[col_order].sort_values(["iso_code", "year"]).reset_index(drop=True)

    validate(df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"\nSaved → {OUTPUT_PATH}")
    print(f"\n{df.to_string(index=False)}")


if __name__ == "__main__":
    main()
