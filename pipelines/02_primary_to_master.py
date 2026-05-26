"""
Pipeline: 02_primary_to_master.py
===================================
Creates the master panel dataset by joining:
  - ai_readiness_2020_2025.parquet   → ai_readiness_score (IV)
  - wgi_2020_2024.parquet            → wgi_composite (Moderator)
  - sdr_2025_overall_score.parquet   → sdg_index_score (DV)

Scope:
  - 26 study countries (Developed / Developing / Lower Governance)
  - Years: 2020, 2021, 2022, 2023
  - Only final index values — no sub-pillar or pillar-level columns

Expected output: 104 rows × 7 columns (26 countries × 4 years)
Join Key (Primary Key): iso_code + year

DQ decisions applied:
  - AI Readiness 2020: total_score IS populated (0 nulls) → included
    (pillar-level columns are null in 2020 but we only need total_score here)
  - AI Readiness sub-pillars and pillar columns: not needed → not included
  - Country name corrections applied before join:
      "United States of America" → "United States"
      "Viet Nam"                 → "Vietnam"
  - Inner join on all three datasets ensures completeness

Country groups (26 countries):
  Developed (10):        Finland, Denmark, Singapore, Germany, Japan,
                         Canada, Netherlands, Norway, Sweden, United States
  Developing (10):       India, Sri Lanka, Brazil, South Africa, Malaysia,
                         China, Indonesia, Mexico, Thailand, Vietnam
  Lower Governance (6):  Nigeria, Bangladesh, Kenya, Pakistan, Ghana, Ethiopia

Outputs:
  data/3_processed_data/master_features/panel_dataset_2020_2023.parquet
  data/3_processed_data/master_features/panel_dataset_2020_2023.csv
"""

import pandas as pd
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent
PRIMARY = ROOT / "data" / "2_primary_data"
OUT_DIR = ROOT / "data" / "3_processed_data" / "master_features"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Study design ─────────────────────────────────────────────────────────────
TARGET_YEARS = [2020, 2021, 2022, 2023]

COUNTRY_META = {
    # country_name: (iso_code, country_group)
    # ── Developed (10) ───────────────────────────────────────────────────────
    "Finland":        ("FIN", "Developed"),
    "Denmark":        ("DNK", "Developed"),
    "Singapore":      ("SGP", "Developed"),
    "Germany":        ("DEU", "Developed"),
    "Japan":          ("JPN", "Developed"),
    "Canada":         ("CAN", "Developed"),
    "Netherlands":    ("NLD", "Developed"),
    "Norway":         ("NOR", "Developed"),
    "Sweden":         ("SWE", "Developed"),
    "United States":  ("USA", "Developed"),
    # ── Developing (10) ──────────────────────────────────────────────────────
    "India":          ("IND", "Developing"),
    "Sri Lanka":      ("LKA", "Developing"),
    "Brazil":         ("BRA", "Developing"),
    "South Africa":   ("ZAF", "Developing"),
    "Malaysia":       ("MYS", "Developing"),
    "China":          ("CHN", "Developing"),
    "Indonesia":      ("IDN", "Developing"),
    "Mexico":         ("MEX", "Developing"),
    "Thailand":       ("THA", "Developing"),
    "Vietnam":        ("VNM", "Developing"),
    # ── Lower Governance (6) ─────────────────────────────────────────────────
    "Nigeria":        ("NGA", "Lower Governance"),
    "Bangladesh":     ("BGD", "Lower Governance"),
    "Kenya":          ("KEN", "Lower Governance"),
    "Pakistan":       ("PAK", "Lower Governance"),
    "Ghana":          ("GHA", "Lower Governance"),
    "Ethiopia":       ("ETH", "Lower Governance"),
}
TARGET_COUNTRY_NAMES = list(COUNTRY_META.keys())
TARGET_ISO_CODES     = [v[0] for v in COUNTRY_META.values()]

AI_COUNTRY_CORRECTIONS = {
    "United States of America": "United States",
    "Viet Nam":                 "Vietnam",
}

# ── 1. Load datasets ─────────────────────────────────────────────────────────
print("Loading primary datasets...")
ai_raw  = pd.read_parquet(PRIMARY / "ai_readiness_2020_2025.parquet")
wgi_raw = pd.read_parquet(PRIMARY / "wgi_2020_2024.parquet")
sdr_raw = pd.read_parquet(PRIMARY / "sdr_2025_overall_score.parquet")

# ── 2. Process AI Readiness ──────────────────────────────────────────────────
print("\n[AI Readiness] Processing...")

ai = ai_raw.copy()
ai["country"] = ai["country"].replace(AI_COUNTRY_CORRECTIONS)
ai = ai[
    (ai["year"].isin(TARGET_YEARS)) &
    (ai["country"].isin(TARGET_COUNTRY_NAMES))
].copy()

# Keep only: year, country, total_score (the final index — IV)
ai = ai[["year", "country", "total_score"]].rename(
    columns={"total_score": "ai_readiness_score"}
)
ai["year"] = ai["year"].astype(int)
print(f"  Rows: {len(ai)} (expected 104)")
print(f"  Nulls in ai_readiness_score: {ai['ai_readiness_score'].isnull().sum()}")

# ── 3. Process WGI ───────────────────────────────────────────────────────────
print("\n[WGI] Processing...")

wgi = wgi_raw[
    (wgi_raw["year"].isin(TARGET_YEARS)) &
    (wgi_raw["iso_code"].isin(TARGET_ISO_CODES))
].copy()

# Keep only: iso_code, country, year, wgi_composite (the final moderator)
wgi = wgi[["iso_code", "country", "year", "wgi_composite"]].copy()
wgi["year"] = wgi["year"].astype(int)
print(f"  Rows: {len(wgi)} (expected 104)")
print(f"  Nulls in wgi_composite: {wgi['wgi_composite'].isnull().sum()}")

# ── 4. Process SDR ───────────────────────────────────────────────────────────
print("\n[SDR] Processing...")

sdr = sdr_raw[
    (sdr_raw["year"].isin(TARGET_YEARS)) &
    (sdr_raw["iso_code"].isin(TARGET_ISO_CODES))
].copy()

# Keep only: iso_code, year, sdr_score (the final DV = SDG index score)
sdr = sdr[["iso_code", "year", "sdr_score"]].rename(
    columns={"sdr_score": "sdg_index_score"}
)
sdr["year"] = sdr["year"].astype(int)
print(f"  Rows: {len(sdr)} (expected 104)")
print(f"  Nulls in sdg_index_score: {sdr['sdg_index_score'].isnull().sum()}")

# ── 5. Join all three datasets ───────────────────────────────────────────────
print("\n[Master] Joining on (iso_code, year)...")

# Base: WGI (has iso_code + country name)
master = wgi.merge(
    sdr,
    on=["iso_code", "year"],
    how="inner",
    validate="1:1",
)

# Bring in AI Readiness via country name (WGI country names match AI Readiness)
master = master.merge(
    ai,
    on=["country", "year"],
    how="inner",
    validate="1:1",
)

print(f"  Master shape before country_group: {master.shape}")

# ── 6. Add country_group ─────────────────────────────────────────────────────
iso_to_group = {iso: grp for _, (iso, grp) in COUNTRY_META.items()}
master["country_group"] = master["iso_code"].map(iso_to_group)

# ── 7. Final column ordering ─────────────────────────────────────────────────
COLUMN_ORDER = [
    "iso_code",
    "country",
    "country_group",
    "year",
    "ai_readiness_score",   # IV  — Oxford Insights AI Readiness Index
    "sdg_index_score",      # DV  — Sustainable Development Report
    "wgi_composite",        # Mod — World Governance Indicators composite
]
master = master[COLUMN_ORDER]
master = master.sort_values(["country_group", "country", "year"]).reset_index(drop=True)

# ── 8. Final DQ check ────────────────────────────────────────────────────────
print("\n[Master] Final DQ checks...")
print(f"  Shape          : {master.shape} (expected 104 × 7)")
print(f"  Countries      : {master['country'].nunique()} (expected 26)")
print(f"  Years          : {sorted(master['year'].unique())} (expected [2020,2021,2022,2023])")
print(f"  Nulls          : {master.isnull().sum().sum()} (expected 0)")
pk_dupes = master.duplicated(subset=["iso_code", "year"]).sum()
print(f"  PK duplicates  : {pk_dupes} (expected 0)")
print(f"\n  Group breakdown:")
print(master.groupby("country_group")["country"].nunique().to_string())

# ── 9. Save ──────────────────────────────────────────────────────────────────
parquet_path = OUT_DIR / "panel_dataset_2020_2023.parquet"
csv_path     = OUT_DIR / "panel_dataset_2020_2023.csv"

master.to_parquet(parquet_path, index=False)
master.to_csv(csv_path, index=False)

print(f"\n✅ Master panel dataset saved:")
print(f"   {parquet_path}")
print(f"   {csv_path}")
print(f"\nPreview (first 12 rows):")
print(master.head(12).to_string(index=False))
