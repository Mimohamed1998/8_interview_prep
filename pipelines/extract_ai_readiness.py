"""
AI Readiness PDF Extractor (2020-2025)
Handles per-year schema differences and produces clean CSV + Parquet.
"""

import re
import pdfplumber
import pandas as pd
from pathlib import Path

BASE = Path(__file__).parent.parent / "data" / "1_raw_data" / "ai_readiness"
OUT  = Path(__file__).parent.parent / "data" / "2_primary_data" / "ai_readiness"
OUT.mkdir(parents=True, exist_ok=True)

issues = []  # (year, issue_type, detail)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean(val):
    if val is None:
        return None
    return str(val).replace("\n", " ").strip()


def fix_squished_name(name):
    """Fix country names where spaces were lost during PDF extraction (2023).

    Three-stage approach:
    1. Pre-split compound connectors ("andthe" → "and the") to avoid
       ambiguity in stage 2.
    2. Split "of"/"and"/"the" when directly adjacent to an uppercase letter.
    3. Split camelCase boundaries (lowercase → uppercase).
    4. Catch any "and"/"of" still directly before a space word boundary.
    """
    if name is None:
        return name
    # Stage 1: compound connectors (e.g. "andthe", "ofthe") — safe to replace
    # unconditionally because no country name has these as substrings of a real word.
    name = re.sub(r"andthe", "and the", name, flags=re.IGNORECASE)
    name = re.sub(r"ofthe", "of the", name, flags=re.IGNORECASE)
    # Stage 2: connectors directly before uppercase (safe — e.g. "andTobago")
    name = re.sub(r"(?<=[a-z])(of|and|the)(?=[A-Z])", r" \1 ", name)
    # Stage 3: camelCase split
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)
    # Stage 4a: connector directly before a space (e.g. "Vincentand the")
    name = re.sub(r"(?<=[a-z])(and|of)(?= )", r" \1", name)
    # Stage 4b: connector directly before a closing paren (e.g. "Stateof)")
    name = re.sub(r"(?<=[a-z])(and|of)(?=\))", r" \1", name)
    # Collapse multiple spaces
    name = re.sub(r"  +", " ", name).strip()
    return name


def safe_float(val):
    try:
        return float(str(val).strip())
    except (ValueError, TypeError):
        return None


def safe_int(val):
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# 2020 – text only, 3 cols: Rank, Country, Score  (no pillar breakdown)
# ---------------------------------------------------------------------------

def parse_2020():
    path = BASE / "ai_readiness_2020.pdf"
    rows = []
    pattern = re.compile(
        r"^(\d+)\s+(.+?)\s+([\d]+\.[\d]+)\s*$"
    )
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                m = pattern.match(line.strip())
                if m:
                    rows.append({
                        "year": 2020,
                        "rank": int(m.group(1)),
                        "country": m.group(2).strip(),
                        "total_score": float(m.group(3)),
                        "government_pillar": None,
                        "technology_sector_pillar": None,
                        "data_infrastructure_pillar": None,
                    })

    issues.append((2020, "MISSING_PILLARS",
        "2020 PDF only reports a single composite score; "
        "government_pillar, technology_sector_pillar, and "
        "data_infrastructure_pillar are absent for this year."))

    df = pd.DataFrame(rows).drop_duplicates(subset=["rank"]).reset_index(drop=True)
    print(f"2020: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 2021 – text only, 5 data cols (country name can span multiple lines)
# ---------------------------------------------------------------------------
# Layout: some country names are split before *and* after the data line:
#   "United States of\n1 88.16 88.46 83.31 92.71\nAmerica"
#   "Lao People's\n114 Democratic 34.93 29.22 24.69 50.88\nRepublic"
# Strategy: process line-by-line with a carry-over buffer for the
# name fragment that precedes the rank.
# ---------------------------------------------------------------------------

def parse_2021():
    path = BASE / "ai_readiness_2021.pdf"
    rows = []
    seen_ranks = set()

    # Regex for a "data line": starts with rank, ends with 4 decimal numbers.
    # Optional middle text is the inline portion of a multi-line country name.
    data_re = re.compile(
        r"^(\d{1,3})\s*(.*?)\s+([\d]+\.[\d]+)\s+([\d]+\.[\d]+)\s+([\d]+\.[\d]+)\s+([\d]+\.[\d]+)\s*$"
    )
    # Header/footer patterns to discard
    noise_re = re.compile(
        r"Government AI Readiness|Annex I|Global Ranking|"
        r"Global\s+Overall|Country\s+Government|Position\s+Score|"
        r"^6[0-9]\s*$|^[0-9]+\s*$"
    )

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = [l.strip() for l in text.splitlines()]
            carry = ""  # name fragment preceding the current data line

            i = 0
            while i < len(lines):
                line = lines[i]
                if not line or noise_re.search(line):
                    carry = ""
                    i += 1
                    continue

                m = data_re.match(line)
                if m:
                    rank   = int(m.group(1))
                    inline = m.group(2).strip()
                    scores = [float(m.group(k)) for k in range(3, 7)]

                    # Suffix rule: only look for a trailing fragment when the
                    # name is still incomplete — i.e. inline is empty (the
                    # country name straddles the data line) OR we already have
                    # a prefix (carry), meaning it's a 3-part name.
                    # When inline is non-empty AND carry is empty the name is
                    # complete on this line; the next fragment belongs to the
                    # following entry as its prefix.
                    suffix = ""
                    if not inline or carry:
                        j = i + 1
                        while j < len(lines) and not lines[j]:
                            j += 1
                        if j < len(lines):
                            nxt = lines[j]
                            if nxt and not noise_re.search(nxt) and not data_re.match(nxt):
                                suffix = nxt
                                i = j  # consume the suffix line

                    parts   = [p for p in [carry, inline, suffix] if p]
                    country = " ".join(parts)
                    carry   = ""

                    if rank not in seen_ranks and rank <= 200:
                        seen_ranks.add(rank)
                        rows.append({
                            "year": 2021,
                            "rank": rank,
                            "country": country,
                            "total_score": scores[0],
                            "government_pillar": scores[1],
                            "technology_sector_pillar": scores[2],
                            "data_infrastructure_pillar": scores[3],
                        })
                else:
                    carry = line

                i += 1

    df = (pd.DataFrame(rows)
          .sort_values("rank")
          .drop_duplicates(subset=["rank"])
          .reset_index(drop=True))

    # Check for wrap-around artefacts in country names
    bad = df[df["country"].str.contains(r"\d", regex=True)]
    if not bad.empty:
        issues.append((2021, "COUNTRY_NAME_NOISE",
            f"{len(bad)} rows have digits in the country name after text parsing "
            f"(likely page-number bleed-through): {bad['country'].tolist()[:5]}"))

    print(f"2021: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 2022 – text only (table extractor only returns column headers, not data)
# ---------------------------------------------------------------------------

def parse_2022():
    path = BASE / "ai_readiness_2022.pdf"
    rows = []
    num = r"[\d]+\.[\d]+"
    pattern = re.compile(
        rf"^(\d{{1,3}})\s+(.+?)\s+({num})\s+({num})\s+({num})\s+({num})\s*$"
    )

    issues.append((2022, "TABLE_EXTRACTION_FAILURE",
        "pdfplumber's table extractor returns only the header row on each page "
        "for this PDF (table borders present but no data rows detected). "
        "Data was recovered via text extraction instead."))

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                m = pattern.match(line.strip())
                if m:
                    rows.append({
                        "year": 2022,
                        "rank": int(m.group(1)),
                        "country": m.group(2).strip(),
                        "total_score": float(m.group(3)),
                        "government_pillar": float(m.group(4)),
                        "technology_sector_pillar": float(m.group(5)),
                        "data_infrastructure_pillar": float(m.group(6)),
                    })

    df = (pd.DataFrame(rows)
          .drop_duplicates(subset=["rank"])
          .sort_values("rank")
          .reset_index(drop=True))
    print(f"2022: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 2023 – table extraction works cleanly
# ---------------------------------------------------------------------------

def parse_2023():
    path = BASE / "ai_readiness_2023.pdf"
    rows = []
    header_seen = False

    # 2023 PDF has a character-encoding quirk: spaces are dropped between
    # words in multi-word country names, producing e.g. "UnitedKingdom".
    # We fix these in a post-processing step and document them.
    squished = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if row is None or len(row) < 6:
                        continue
                    rank_raw = clean(row[0])
                    if not rank_raw or not rank_raw.replace(" ", "").isdigit():
                        if not header_seen:
                            header_seen = True
                        continue
                    rank = safe_int(rank_raw)
                    if rank is None:
                        continue
                    raw_country = clean(row[1])
                    fixed = fix_squished_name(raw_country)
                    if fixed != raw_country:
                        squished.append((rank, raw_country, fixed))
                    rows.append({
                        "year": 2023,
                        "rank": rank,
                        "country": fixed,
                        "total_score": safe_float(row[2]),
                        "government_pillar": safe_float(row[3]),
                        "technology_sector_pillar": safe_float(row[4]),
                        "data_infrastructure_pillar": safe_float(row[5]),
                    })

    if squished:
        examples = [(r, orig, fix) for r, orig, fix in squished[:6]]
        issues.append((2023, "SQUISHED_COUNTRY_NAMES",
            f"2023 PDF lost spaces in {len(squished)} multi-word country names "
            f"(PDF character-encoding artefact). Auto-fixed via camelCase splitting "
            f"and connector-word insertion. Examples (rank, raw→fixed): "
            + "; ".join(f"{r}: '{o}'→'{f}'" for r, o, f in examples)))

    df = (pd.DataFrame(rows)
          .drop_duplicates(subset=["rank"])
          .sort_values("rank")
          .reset_index(drop=True))
    print(f"2023: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 2024 – table works but NO rank column (alphabetical order)
# ---------------------------------------------------------------------------

def parse_2024():
    path = BASE / "ai_readiness_2024.pdf"
    rows = []
    header_cols = ["Country", "Total", "Government", "Technology\nSector", "Dataand\nInfrastructure"]

    issues.append((2024, "MISSING_RANK_COLUMN",
        "2024 PDF presents countries in alphabetical order with no "
        "rank/global-position column. Rank has been inferred by sorting "
        "total_score descending and assigning dense rank."))

    squished_2024 = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if row is None or len(row) < 5:
                        continue
                    raw_country = clean(row[0])
                    if raw_country in ("Country", None, ""):
                        continue
                    score = safe_float(row[1])
                    if score is None:
                        continue
                    fixed = fix_squished_name(raw_country)
                    if fixed != raw_country:
                        squished_2024.append((raw_country, fixed))
                    rows.append({
                        "year": 2024,
                        "country": fixed,
                        "total_score": score,
                        "government_pillar": safe_float(row[2]),
                        "technology_sector_pillar": safe_float(row[3]),
                        "data_infrastructure_pillar": safe_float(row[4]),
                    })

    if squished_2024:
        issues.append((2024, "SQUISHED_COUNTRY_NAMES",
            f"2024 PDF lost spaces in {len(squished_2024)} multi-word country names "
            f"(same PDF character-encoding artefact as 2023). Auto-fixed. "
            f"Examples: {squished_2024[:4]}"))

    df = pd.DataFrame(rows).drop_duplicates(subset=["country"]).reset_index(drop=True)
    # Infer rank from score
    df["rank"] = df["total_score"].rank(method="min", ascending=False).astype(int)
    df = df[["year", "rank", "country", "total_score",
             "government_pillar", "technology_sector_pillar", "data_infrastructure_pillar"]]
    df = df.sort_values("rank").reset_index(drop=True)
    print(f"2024: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# 2025 – table works, but completely different pillar schema
# ---------------------------------------------------------------------------

def parse_2025():
    path = BASE / "ai_readiness_2025.pdf"
    rows = []

    issues.append((2025, "SCHEMA_CHANGE_NEW_PILLARS",
        "2025 introduced a new 6-pillar framework replacing the 2020-2024 "
        "3-pillar model. New columns: policy_capacity, ai_infrastructure, "
        "governance, public_sector_adoption, development_diffusion, resilience. "
        "The old government_pillar / technology_sector_pillar / "
        "data_infrastructure_pillar columns are NULL for 2025."))

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if row is None or len(row) < 8:
                        continue
                    country = clean(row[0])
                    if country in ("Country", None, ""):
                        continue
                    rank = safe_int(row[1])
                    if rank is None:
                        continue
                    rows.append({
                        "year": 2025,
                        "rank": rank,
                        "country": country,
                        "total_score": None,
                        "government_pillar": None,
                        "technology_sector_pillar": None,
                        "data_infrastructure_pillar": None,
                        "policy_capacity": safe_float(row[2]),
                        "ai_infrastructure": safe_float(row[3]),
                        "governance": safe_float(row[4]),
                        "public_sector_adoption": safe_float(row[5]),
                        "development_diffusion": safe_float(row[6]),
                        "resilience": safe_float(row[7]),
                    })

    df = (pd.DataFrame(rows)
          .drop_duplicates(subset=["country"])
          .sort_values("rank")
          .reset_index(drop=True))
    print(f"2025: {len(df)} rows")
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    frames_2020_2024 = [parse_2020(), parse_2021(), parse_2022(), parse_2023(), parse_2024()]
    df_2025 = parse_2025()

    # Combined 2020-2024 with shared schema
    combined = pd.concat(frames_2020_2024, ignore_index=True)

    # Add 2025 columns (NaN for old pillars already set in parse_2025)
    full = pd.concat([combined, df_2025], ignore_index=True)

    # Canonical column order
    cols = [
        "year", "rank", "country",
        "total_score",
        "government_pillar", "technology_sector_pillar", "data_infrastructure_pillar",
        "policy_capacity", "ai_infrastructure", "governance",
        "public_sector_adoption", "development_diffusion", "resilience",
    ]
    full = full.reindex(columns=cols)

    # Check for duplicate (year, country) pairs
    dupes = full[full.duplicated(subset=["year", "country"], keep=False)]
    if not dupes.empty:
        issues.append(("ALL", "DUPLICATE_YEAR_COUNTRY",
            f"{len(dupes)} rows share the same (year, country) key: "
            f"{dupes[['year','country']].drop_duplicates().values.tolist()[:10]}"))

    # Check for null scores in 2020-2024
    missing_score = full[(full["year"] < 2025) & full["total_score"].isna()]
    if not missing_score.empty:
        issues.append(("ALL", "NULL_TOTAL_SCORE",
            f"{len(missing_score)} rows in 2020-2024 have null total_score."))

    # Country name consistency check
    all_countries = full.groupby("country")["year"].nunique()
    sporadic = all_countries[all_countries < 3].index.tolist()
    if sporadic:
        issues.append(("ALL", "COUNTRY_NAME_INCONSISTENCY",
            f"{len(sporadic)} country names appear in fewer than 3 years — "
            "likely caused by spelling variation across editions. "
            f"Examples: {sporadic[:15]}"))

    # Write outputs
    out_csv = OUT / "ai_readiness_2020_2025.csv"
    out_parquet = OUT / "ai_readiness_2020_2025.parquet"
    full.to_csv(out_csv, index=False)
    full.to_parquet(out_parquet, index=False)
    print(f"\nWrote {len(full)} rows -> {out_csv}")
    print(f"Wrote {len(full)} rows -> {out_parquet}")

    # Print issues summary
    print(f"\n{'='*60}")
    print(f"DQ ISSUES ({len(issues)} total)")
    print(f"{'='*60}")
    for year, itype, detail in issues:
        print(f"[{year}] {itype}\n  {detail}\n")

    return full, issues


if __name__ == "__main__":
    df, dq = main()
