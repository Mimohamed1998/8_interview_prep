"""Export pipeline — writes inference predictions as CSVs at cell, merged, and item level."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.common.utils.config import load_config


def _load_merged(parquet_path: str) -> pd.DataFrame:
    """Join buffered predictions with cell_name and return the flat merged frame."""
    buffered = pd.read_parquet(f"{parquet_path}/predictions_buffered.parquet")
    cell_names = pd.read_parquet(
        f"{parquet_path}/predictions.parquet",
        columns=["outlet_id", "item_code", "year_month", "cell_name"],
    )
    return buffered.merge(cell_names, on=["outlet_id", "item_code", "year_month"], how="left")


def write_per_cell_csvs(df: pd.DataFrame, output_path: str) -> None:
    """Write one CSV per cell cluster."""
    out_cols = [
        "outlet_id", "item_code", "year_month",
        "predicted_qty", "buffer", "buffered_forecast", "cell_name",
    ]
    for cell, group in df.groupby("cell_name", observed=True):
        filepath = f"{output_path}/{cell}.csv"
        group[out_cols].to_csv(filepath, index=False)
        print(f"  [{cell}]  {len(group):>10,} rows → {filepath}")


def write_merged_csv(df: pd.DataFrame, output_path: str) -> None:
    """Write all rows into a single merged CSV with cell_name as the cluster column."""
    out_cols = [
        "outlet_id", "item_code", "year_month",
        "predicted_qty", "buffer", "buffered_forecast", "cell_name",
    ]
    filepath = f"{output_path}/inference_merged.csv"
    df[out_cols].to_csv(filepath, index=False)
    print(f"  [merged]  {len(df):>10,} rows → {filepath}")


def write_item_level_csv(df: pd.DataFrame, output_path: str, cell_data_path: str) -> None:
    """Aggregate to item × year_month level and write CSV.

    Outlet dimension and outlet cluster are removed. Each item's demand_class
    (Continuous / Intermittent / Lumpy) is joined as the retained cluster label.
    Volumes are summed across all outlets.
    """
    item_meta = pd.read_parquet(
        f"{cell_data_path}/item_classification.parquet",
        columns=["item_code", "demand_class"],
    )

    item_df = (
        df.groupby(["item_code", "year_month"], observed=True)
        .agg(
            actual_qty=("actual_qty", "sum"),
            predicted_qty=("predicted_qty", "sum"),
            buffer=("buffer", "sum"),
            buffered_forecast=("buffered_forecast", "sum"),
        )
        .reset_index()
        .merge(item_meta, on="item_code", how="left")
    )

    out_cols = [
        "item_code", "year_month",
        "actual_qty", "predicted_qty", "buffer", "buffered_forecast",
        "demand_class",
    ]
    filepath = f"{output_path}/inference_item_level.csv"
    item_df[out_cols].to_csv(filepath, index=False)
    print(f"  [item-level]  {len(item_df):>8,} rows → {filepath}")


def main():
    cfg = load_config()
    inf_cfg = cfg["inference"]

    parquet_path = inf_cfg["output_path"]
    output_path = inf_cfg["csv_output_path"]

    Path(output_path).mkdir(parents=True, exist_ok=True)

    print("Loading data...")
    df = _load_merged(parquet_path)

    print("\nWriting per-cell CSVs:")
    write_per_cell_csvs(df, output_path)

    print("\nWriting merged CSV:")
    write_merged_csv(df, output_path)

    print("\nWriting item-level CSV:")
    write_item_level_csv(df, output_path, inf_cfg["cell_data_path"])

    print(f"\nDone → {output_path}/")


if __name__ == "__main__":
    main()
