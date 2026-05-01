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


def create_base_sales_enriched(sales_df: pd.DataFrame, product_df: pd.DataFrame, region_df: pd.DataFrame) -> pd.DataFrame:
    """Create the base_sales_enriched dataset by joining sales with product and region.

    Args:
        sales_df: Processed sales DataFrame.
        product_df: Processed product DataFrame.
        region_df: Processed region DataFrame.

    Returns:
        Enriched sales DataFrame with product and region information.
    """
    sales_df = sales_df.copy()
    sales_df["document_date"] = pd.to_datetime(sales_df["document_date"], format="%Y_%m_%d")
    sales_df["year_month"] = sales_df["document_date"].dt.strftime("%Y-%m")

    df = sales_df.merge(product_df, on="item_code", how="left")
    df = df.merge(region_df, on="territory_id", how="left")

    return df


def create_outlet_sku_monthly_demand(base_sales_enriched_df: pd.DataFrame) -> pd.DataFrame:
    """Create the outlet_sku_monthly_demand dataset with fully populated monthly demand.

    Args:
        base_sales_enriched_df: Base sales enriched DataFrame.

    Returns:
        DataFrame with monthly demand for each outlet-SKU pair.
    """
    # Build date spine
    min_date = base_sales_enriched_df["document_date"].min()
    max_date = base_sales_enriched_df["document_date"].max()
    date_spine = pd.date_range(start=min_date, end=max_date, freq="MS").strftime("%Y-%m").tolist()

    # Build active outlet-SKU spine
    active_pairs = base_sales_enriched_df[base_sales_enriched_df["document_type"] == "invoice"][["outlet_id", "item_code"]].drop_duplicates()

    # Cross join
    outlet_sku_spine = active_pairs.assign(key=1)
    date_spine_df = pd.DataFrame({"year_month": date_spine, "key": 1})
    full_grid = outlet_sku_spine.merge(date_spine_df, on="key").drop("key", axis=1)

    # Aggregate actual demand
    agg_df = base_sales_enriched_df.groupby(["outlet_id", "item_code", "year_month"]).agg(
        net_quantity=("quantity", "sum"),
        net_sales=("net_sales", "sum"),
        gross_quantity=("quantity", lambda x: x[x > 0].sum()),
        gross_sales=("net_sales", lambda x: x[x > 0].sum()),
        return_quantity=("quantity", lambda x: abs(x[x < 0].sum())),
        return_sales=("net_sales", lambda x: abs(x[x < 0].sum())),
        n_invoices=("document_type", lambda x: (x == "invoice").sum()),
        n_returns=("document_type", lambda x: (x == "return").sum())
    ).reset_index()

    # Left join onto full grid
    df = full_grid.merge(agg_df, on=["outlet_id", "item_code", "year_month"], how="left")
    df = df.fillna(0)

    # Add dimensions
    dims = base_sales_enriched_df[["outlet_id", "territory_id", "region", "district", "province", "item_code", "product_category", "product_line", "brand"]].drop_duplicates()
    df = df.merge(dims, on=["outlet_id", "item_code"], how="left")

    return df


def create_outlet_monthly_activity(base_sales_enriched_df: pd.DataFrame) -> pd.DataFrame:
    """Create the outlet_monthly_activity dataset with monthly activity per outlet.

    Args:
        base_sales_enriched_df: Base sales enriched DataFrame.

    Returns:
        DataFrame with monthly activity for each outlet.
    """
    # Date spine
    min_date = base_sales_enriched_df["document_date"].min()
    max_date = base_sales_enriched_df["document_date"].max()
    date_spine = pd.date_range(start=min_date, end=max_date, freq="MS").strftime("%Y-%m").tolist()

    # Outlet spine
    outlets = base_sales_enriched_df["outlet_id"].drop_duplicates()

    # Cross join
    outlet_spine = outlets.to_frame().assign(key=1)
    date_spine_df = pd.DataFrame({"year_month": date_spine, "key": 1})
    full_grid = outlet_spine.merge(date_spine_df, on="key").drop("key", axis=1)

    # Aggregate activity
    agg_df = base_sales_enriched_df.groupby(["outlet_id", "year_month"]).agg(
        n_invoices=("document_type", lambda x: (x == "invoice").sum()),
        gross_quantity=("quantity", lambda x: x[x > 0].sum()),
        gross_sales=("net_sales", lambda x: x[x > 0].sum()),
        n_returns=("document_type", lambda x: (x == "return").sum()),
        return_quantity=("quantity", lambda x: abs(x[x < 0].sum())),
        return_sales=("net_sales", lambda x: abs(x[x < 0].sum())),
        n_unique_skus=("item_code", "nunique"),
        n_unique_categories=("product_category", "nunique"),
        primary_payment_term=("payment_term", lambda x: x.mode().iloc[0] if not x.empty else "unknown")
    ).reset_index()

    # Left join
    df = full_grid.merge(agg_df, on=["outlet_id", "year_month"], how="left")
    df = df.fillna({"n_invoices": 0, "gross_quantity": 0, "gross_sales": 0, "n_returns": 0, "return_quantity": 0, "return_sales": 0, "n_unique_skus": 0, "n_unique_categories": 0, "primary_payment_term": "unknown"})

    # Add dimensions
    dims = base_sales_enriched_df[["outlet_id", "territory_id", "region", "district", "province"]].drop_duplicates()
    df = df.merge(dims, on="outlet_id", how="left")

    return df


def create_monthly_territory_demand(outlet_sku_monthly_demand_df: pd.DataFrame, region_df: pd.DataFrame) -> pd.DataFrame:
    """Create the monthly_territory_demand dataset aggregated to territory level.

    Args:
        outlet_sku_monthly_demand_df: Outlet SKU monthly demand DataFrame.
        region_df: Processed region DataFrame.

    Returns:
        DataFrame with monthly demand aggregated by territory.
    """
    # Date spine
    date_spine = outlet_sku_monthly_demand_df["year_month"].drop_duplicates().sort_values().tolist()

    # Territory spine
    territories = region_df["territory_id"].drop_duplicates()

    # Cross join
    territory_spine = territories.to_frame().assign(key=1)
    date_spine_df = pd.DataFrame({"year_month": date_spine, "key": 1})
    full_grid = territory_spine.merge(date_spine_df, on="key").drop("key", axis=1)

    # Aggregate
    agg_df = outlet_sku_monthly_demand_df.groupby(["year_month", "territory_id"]).agg(
        net_quantity=("net_quantity", "sum"),
        net_sales=("net_sales", "sum"),
        gross_quantity=("gross_quantity", "sum"),
        gross_sales=("gross_sales", "sum"),
        return_quantity=("return_quantity", "sum"),
        return_sales=("return_sales", "sum"),
        n_unique_skus=("item_code", lambda x: (x > 0).sum())  # where n_invoices > 0
    ).reset_index()

    # Left join
    df = full_grid.merge(agg_df, on=["year_month", "territory_id"], how="left")
    df = df.fillna(0)

    # Add dimensions
    df = df.merge(region_df, on="territory_id", how="left")

    return df


def create_outlet_features(outlet_monthly_activity_df: pd.DataFrame) -> pd.DataFrame:
    """Create the outlet_features dataset for clustering.

    Args:
        outlet_monthly_activity_df: Outlet monthly activity DataFrame.

    Returns:
        DataFrame with features for each outlet.
    """
    # Define window: last 12 months
    max_month = outlet_monthly_activity_df["year_month"].max()
    window_start = pd.to_datetime(max_month + "-01") - pd.DateOffset(months=11)
    window_end = pd.to_datetime(max_month + "-01")
    window_months = pd.date_range(start=window_start, end=window_end, freq="MS").strftime("%Y-%m").tolist()

    # Filter to window
    window_df = outlet_monthly_activity_df[outlet_monthly_activity_df["year_month"].isin(window_months)]

    # Aggregate to outlet
    features_df = window_df.groupby("outlet_id").agg(
        total_net_sales=("gross_sales", "sum"),
        total_quantity=("gross_quantity", "sum"),
        active_months=("n_invoices", lambda x: (x > 0).sum()),
        loyalty_ratio=("n_invoices", lambda x: (x > 0).sum() / 12),
        avg_txn_per_active_month=("n_invoices", lambda x: x.sum() / (x > 0).sum() if (x > 0).sum() > 0 else 0),
        avg_net_sales_per_txn=("gross_sales", lambda x: x.sum() / x[x > 0].count() if (x > 0).count() > 0 else 0),
        avg_qty_per_txn=("gross_quantity", lambda x: x.sum() / x[x > 0].count() if (x > 0).count() > 0 else 0),
        n_unique_skus=("n_unique_skus", "max"),
        n_unique_categories=("n_unique_categories", "max"),
        return_rate=("n_returns", lambda x: x.sum() / (x[x > 0].count() + x.sum()) if (x[x > 0].count() + x.sum()) > 0 else 0),
        recency_months=("year_month", lambda x: (pd.to_datetime(max_month + "-01") - pd.to_datetime(x.max() + "-01")).days // 30 if not x.empty else 12),
        momentum=("gross_sales", lambda x: x.iloc[-3:].sum() / x.iloc[:-3].sum() if len(x) >= 6 and x.iloc[:-3].sum() > 0 else 0),
        pct_cash_txn=("primary_payment_term", lambda x: (x == "cash").sum() / len(x) if len(x) > 0 else 0)
    ).reset_index()

    # Add is_active
    features_df["is_active"] = features_df["active_months"] >= 1

    # Add dimensions
    dims = outlet_monthly_activity_df[["outlet_id", "territory_id", "region", "province"]].drop_duplicates()
    df = features_df.merge(dims, on="outlet_id", how="left")

    return df
