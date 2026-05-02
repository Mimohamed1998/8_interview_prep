import pandas as pd
from pathlib import Path


def load_cell(matrix_path, cluster_name, demand_class):
    """Load and filter the modeling matrix to a single grid cell.

    Returns:
        pandas DataFrame filtered to the requested cell, null targets dropped.
    """
    df = pd.read_parquet(Path(matrix_path))
    df = df[
        (df["cluster_definition"] == cluster_name) &
        (df["demand_class"] == demand_class)
    ].copy()
    # Drop rows where both regression targets are null (last 2 rows per series)
    df = df.dropna(subset=["target_qty_log1p", "target_qty_raw"])
    df = df.reset_index(drop=True)
    return df
