"""Dataset-specific transformation functions for the raw processing pipeline."""

import re
import pandas as pd
from typing import Dict, Any


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Rename all columns to snake_case with no special characters.

    Converts to lowercase, strips leading/trailing whitespace, replaces
    internal whitespace and hyphens with underscores, and removes any
    remaining characters that are not alphanumeric or underscore.

    Args:
        df: Input DataFrame with raw column names.

    Returns:
        DataFrame with standardized column names.
    """
    def _clean(name: str) -> str:
        name = name.strip()
        # camelCase / PascalCase → snake_case before lowercasing
        name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
        name = name.lower()
        name = re.sub(r"[\s\-]+", "_", name)
        name = re.sub(r"[^\w]", "", name)
        name = name.strip("_")
        return name

    df = df.copy()
    df.columns = [_clean(c) for c in df.columns]
    return df


def standardize_categorical_values(df: pd.DataFrame) -> pd.DataFrame:
    """Clean string values in all object-dtype columns to snake_case.

    Converts to lowercase, strips leading/trailing whitespace, replaces
    internal whitespace and hyphens with underscores, and removes any
    remaining characters that are not alphanumeric or underscore.

    Args:
        df: Input DataFrame after column name standardization.

    Returns:
        DataFrame with standardized categorical values.
    """
    def _clean_value(val: str) -> str:
        val = val.strip().lower()
        val = re.sub(r"[\s\-]+", "_", val)
        val = re.sub(r"[^\w]", "", val)
        val = val.strip("_")
        return val

    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].apply(lambda x: _clean_value(str(x)) if pd.notna(x) else x)
    return df


def process_region(df: pd.DataFrame, conf: Dict[str, Any]) -> pd.DataFrame:
    """Process the region mapping dataset.

    Steps:
        1. Standardize column names.
        2. Standardize categorical values.
        3. Cast TerritoryID column(s) to string.

    Args:
        df: Raw region mapping DataFrame.
        conf: Full configuration dictionary loaded from conf.yml.

    Returns:
        Processed region DataFrame.
    """
    df = standardize_column_names(df)
    df = standardize_categorical_values(df)
    for col in conf["raw_processing"]["region"]["id_columns_to_str"]:
        df[col] = df[col].astype(str)
    return df


def process_product(df: pd.DataFrame, conf: Dict[str, Any]) -> pd.DataFrame:
    """Process the product mapping dataset.

    Steps:
        1. Standardize column names.
        2. Standardize categorical values.

    Args:
        df: Raw product mapping DataFrame.
        conf: Full configuration dictionary loaded from conf.yml.

    Returns:
        Processed product DataFrame.
    """
    df = standardize_column_names(df)
    df = standardize_categorical_values(df)
    return df


def process_sales(df: pd.DataFrame, conf: Dict[str, Any]) -> pd.DataFrame:
    """Process the invoice-level sales dataset.

    Steps:
        1. Standardize column names.
        2. Standardize categorical values.
        3. Cast ID columns to string.
        4. Drop excluded columns.
        5. Make Quantity negative for return document types.

    Args:
        df: Raw sales DataFrame.
        conf: Full configuration dictionary loaded from conf.yml.

    Returns:
        Processed sales DataFrame.
    """
    sales_conf = conf["raw_processing"]["sales"]

    df = standardize_column_names(df)
    df = standardize_categorical_values(df)

    for col in sales_conf["id_columns_to_str"]:
        df[col] = df[col].astype(str)

    df = df.drop(columns=sales_conf["drop_columns"])

    return_type = sales_conf["return_document_type"]
    df.loc[df["document_type"] == return_type, "quantity"] = (
        df.loc[df["document_type"] == return_type, "quantity"] * -1
    )

    return df
