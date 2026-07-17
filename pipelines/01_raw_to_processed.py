"""
Raw -> Processed data cleaning pipeline.

Source files (data/raw/):
  - Economic Recillience Index.csv
  - Main Data Sheet.csv
  - Market Diversification Index.csv
  - Product Diversification Index.csv

Output files (data/processed/):
  - economic_resilience_index.csv
  - economic_indicators_yearly.csv
  - market_diversification_exports_by_country.csv
  - product_diversification_exports_by_category.csv

Raw quirks handled:
  - Trailing whitespace on several headers ("Exchange Rate ", "Thailand ",
    "Total exports ")
  - Thousand-separator commas quoted as strings in numeric columns
    (Market Diversification Index, Product Diversification Index)
  - Product Diversification Index has a blank leading index column and a
    mislabeled second header ("Value in USD mn") that actually holds
    product category names
  - Inconsistent header casing/spelling ("netherland" -> "netherlands")
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

ERI_RAW = RAW_DIR / "Economic Recillience Index.csv"
MAIN_RAW = RAW_DIR / "Main Data Sheet.csv"
MDI_RAW = RAW_DIR / "Market Diversification Index.csv"
PDI_RAW = RAW_DIR / "Product Diversification Index.csv"

ERI_OUT = PROCESSED_DIR / "economic_resilience_index.csv"
MAIN_OUT = PROCESSED_DIR / "economic_indicators_yearly.csv"
MDI_OUT = PROCESSED_DIR / "market_diversification_exports_by_country.csv"
PDI_OUT = PROCESSED_DIR / "product_diversification_exports_by_category.csv"


def _to_number(series: pd.Series) -> pd.Series:
    """Strip thousand-separator commas and cast to float."""
    return series.astype(str).str.replace(",", "", regex=False).str.strip().astype(float)


def _process_eri() -> pd.DataFrame:
    df = pd.read_csv(ERI_RAW)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "Year": "year",
        "GDP Growth (%)": "gdp_growth_pct",
        "Unemployment (%)": "unemployment_pct",
        "TB Ratio (% GDP)": "trade_balance_pct_gdp",
        "N_GDP": "n_gdp",
        "N_Unemp (inv)": "n_unemployment_inv",
        "N_TB (inv)": "n_trade_balance_inv",
        "ERI": "eri",
    })
    df["year"] = df["year"].astype(int)
    return df.sort_values("year").reset_index(drop=True)


def _process_main() -> pd.DataFrame:
    df = pd.read_csv(MAIN_RAW)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "year": "year",
        "Economic Recillience Index (IRI)": "economic_resilience_index",
        "Product Diversification Index (PDI)": "product_diversification_index",
        "Market diversification Index (MDI)": "market_diversification_index",
        "Inflation Rate": "inflation_rate_pct",
        "FDI (USD) Foreign direct investment, net inflows (BoP, current US$)": "fdi_net_inflows_usd",
        "Exchange Rate": "exchange_rate",
    })
    df["year"] = df["year"].astype(int)
    return df.sort_values("year").reset_index(drop=True)


def _process_mdi() -> pd.DataFrame:
    df = pd.read_csv(MDI_RAW)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={
        "year": "year",
        "USA": "usa",
        "UK": "uk",
        "Italy": "italy",
        "UAE": "uae",
        "netherland": "netherlands",
        "China": "china",
        "Japan": "japan",
        "france": "france",
        "Turkey": "turkey",
        "Canada": "canada",
        "Australia": "australia",
        "Saudi Arabia": "saudi_arabia",
        "Singapore": "singapore",
        "South Korea": "south_korea",
        "Malaysia": "malaysia",
        "Thailand": "thailand",
        "Spain": "spain",
        "Qatar": "qatar",
        "Kuwait": "kuwait",
        "Germany": "germany",
        "Russia": "russia",
        "Total exports": "total_exports",
    })
    value_cols = [c for c in df.columns if c != "year"]
    for col in value_cols:
        df[col] = _to_number(df[col])
    df["year"] = df["year"].astype(int)
    return df.sort_values("year").reset_index(drop=True)


def _process_pdi() -> pd.DataFrame:
    df = pd.read_csv(PDI_RAW)
    df.columns = [c.strip() for c in df.columns]
    # Col 0 is a blank leading index column from the raw export; col 1's
    # header ("Value in USD mn") is mislabeled and actually holds product
    # category names, not units.
    df = df.drop(columns=[df.columns[0]])
    df = df.rename(columns={df.columns[0]: "product_category"})
    df.columns = [df.columns[0]] + [str(c).strip() for c in df.columns[1:]]
    year_cols = df.columns[1:]
    for col in year_cols:
        df[col] = _to_number(df[col])
    df["product_category"] = df["product_category"].str.strip()
    return df.reset_index(drop=True)


def _validate(name: str, df: pd.DataFrame) -> None:
    assert df.shape[0] > 0, f"{name}: no rows"
    assert not df.columns.duplicated().any(), f"{name}: duplicate columns"
    bad_cols = [c for c in df.columns if c != c.strip().lower() or " " in c]
    assert not bad_cols, f"{name}: non-snake_case columns {bad_cols}"


def run() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    jobs = [
        ("economic_resilience_index", _process_eri, ERI_OUT),
        ("economic_indicators_yearly", _process_main, MAIN_OUT),
        ("market_diversification_exports_by_country", _process_mdi, MDI_OUT),
        ("product_diversification_exports_by_category", _process_pdi, PDI_OUT),
    ]

    for name, fn, out_path in jobs:
        print(f"Processing: {name}")
        df = fn()
        _validate(name, df)
        df.to_csv(out_path, index=False)
        size_kb = out_path.stat().st_size / 1024
        print(f"Written -> {out_path} ({df.shape[0]} rows x {df.shape[1]} cols, {size_kb:.1f} KB)")


if __name__ == "__main__":
    run()
