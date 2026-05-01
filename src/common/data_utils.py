"""Standardised I/O helpers for reading and writing data files."""

import pandas as pd
from pathlib import Path


def read_csv(path: str) -> pd.DataFrame:
    """Read a CSV file into a DataFrame.

    Args:
        path: Path to the CSV file.

    Returns:
        DataFrame containing the file contents.
    """
    return pd.read_csv(path)


def read_parquet(path: str) -> pd.DataFrame:
    """Read a parquet file into a DataFrame.

    Args:
        path: Path to the parquet file.

    Returns:
        DataFrame containing the file contents.
    """
    return pd.read_parquet(path)


def write_parquet(df: pd.DataFrame, path: str) -> None:
    """Write a DataFrame to a parquet file, creating parent directories as needed.

    Args:
        df: DataFrame to write.
        path: Destination path for the parquet file.
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
