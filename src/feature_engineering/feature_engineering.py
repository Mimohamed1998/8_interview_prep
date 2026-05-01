"""
Feature engineering functions using Polars.
"""

import math
import polars as pl
from typing import Dict


def build_seasonal_index(demand_path: str, training_start: str, training_end: str) -> pl.DataFrame:
    """Compute per-(item_code, month_int) seasonal index from national training demand.
    
    Args:
        demand_path: Path to the demand parquet file.
        training_start: Start month of the training window (YYYY-MM).
        training_end: End month of the training window (YYYY-MM).
        
    Returns:
        DataFrame with item_code, month_int, seasonal_index.
    """
    df = (
        pl.scan_parquet(demand_path)
        .filter((pl.col("year_month") >= training_start) & (pl.col("year_month") <= training_end))
        .with_columns(
            pl.col("year_month").str.slice(5, 2).cast(pl.Int32).alias("month_int")
        )
        .group_by(["item_code", "month_int"])
        .agg(pl.col("net_quantity").mean().alias("mean_qty_month"))
        .collect()
    )
    
    mean_all = df.group_by("item_code").agg(pl.col("mean_qty_month").mean().alias("mean_qty_all_months"))
    
    return (
        df.join(mean_all, on="item_code")
        .with_columns((pl.col("mean_qty_month") / pl.col("mean_qty_all_months")).alias("seasonal_index"))
        .select(["item_code", "month_int", "seasonal_index"])
    )


def build_enriched_sku_features(sku_continuity_df: pl.DataFrame, item_class_df: pl.DataFrame) -> pl.DataFrame:
    """Join demand_class onto SKU continuity features.
    
    Args:
        sku_continuity_df: DataFrame containing SKU continuity metrics.
        item_class_df: DataFrame containing authoritative item classifications.
        
    Returns:
        DataFrame with enriched SKU features.
    """
    if "demand_class" in sku_continuity_df.columns:
        sku_continuity_df = sku_continuity_df.drop("demand_class")
        
    res = (
        sku_continuity_df.join(item_class_df, on="item_code", how="left")
        .with_columns([
            pl.col("demand_class").replace({"Continuous": 0, "Intermittent": 1, "Lumpy": 2}).cast(pl.Int8).alias("demand_class_encoded"),
            (pl.col("product_line") == "prod_line3").cast(pl.Int8).alias("is_structural_collapse"),
            (pl.col("product_line") == "prod_line17").cast(pl.Int8).alias("is_hyper_growth"),
            pl.col("total_quantity").log1p().alias("sku_log_total_qty"),
            pl.col("activity_rate").alias("sku_activity_rate"),
            pl.col("cv").alias("sku_cv")
        ])
        .select(["item_code", "demand_class", "demand_class_encoded", "sku_activity_rate", "sku_cv", "is_structural_collapse", "is_hyper_growth", "sku_log_total_qty"])
    )
    return res


def build_territory_context(territory_df: pl.DataFrame) -> pl.DataFrame:
    """Build territory context features.
    
    Args:
        territory_df: DataFrame containing territory metrics.
        
    Returns:
        DataFrame with territory features.
    """
    return (
        territory_df.lazy()
        .select(["territory_id", "year_month", "net_quantity", "net_sales"])
        .rename({"net_quantity": "terr_net_quantity", "net_sales": "terr_net_sales"})
        .sort(["territory_id", "year_month"])
        .with_columns([
            pl.col("terr_net_quantity").shift(1).over("territory_id").alias("terr_lag_qty_1m"),
            pl.col("terr_net_quantity").rolling_mean(3, min_periods=1).over("territory_id").alias("terr_roll_mean_qty_3m")
        ])
        .collect()
    )


def build_base_lazy(demand_path: str, cluster_df: pl.DataFrame, training_start: str, training_end: str) -> pl.LazyFrame:
    """Build base lazyframe from demand data.
    
    Args:
        demand_path: Path to the demand parquet file.
        cluster_df: DataFrame containing outlet clusters.
        training_start: Start month of training window.
        training_end: End month of training window.
        
    Returns:
        LazyFrame with base data filtered and sorted.
    """
    return (
        pl.scan_parquet(demand_path)
        .filter((pl.col("year_month") >= training_start) & (pl.col("year_month") <= training_end))
        .join(cluster_df.lazy(), on="outlet_id", how="left")
        .filter(pl.col("cluster_definition").is_in(['Power', 'High-Value Active', 'Low-Value Sporadic']))
        .sort(["outlet_id", "item_code", "year_month"])
    )


def build_time_features(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Build time and seasonal features.
    
    Args:
        lf: Base LazyFrame.
        
    Returns:
        LazyFrame with added time features.
    """
    return lf.with_columns([
        pl.col("year_month").str.slice(0, 4).cast(pl.Int32).alias("year"),
        pl.col("year_month").str.slice(5, 2).cast(pl.Int32).alias("month_int")
    ]).with_columns([
        ((pl.col("year") - 2015) * 12 + pl.col("month_int")).alias("months_elapsed"),
        (2 * math.pi * 1 * pl.col("month_int") / 12).sin().alias("sin_1"),
        (2 * math.pi * 1 * pl.col("month_int") / 12).cos().alias("cos_1"),
        (2 * math.pi * 2 * pl.col("month_int") / 12).sin().alias("sin_2"),
        (2 * math.pi * 2 * pl.col("month_int") / 12).cos().alias("cos_2"),
        (2 * math.pi * 3 * pl.col("month_int") / 12).sin().alias("sin_3"),
        (2 * math.pi * 3 * pl.col("month_int") / 12).cos().alias("cos_3"),
        (pl.col("month_int") == 10).cast(pl.Int8).alias("is_peak_month"),
        (pl.col("month_int") == 4).cast(pl.Int8).alias("is_trough_month")
    ])


def build_lag_rolling_features(lf: pl.LazyFrame) -> pl.LazyFrame:
    """Build lag and rolling window features.
    
    Args:
        lf: LazyFrame with base data.
        
    Returns:
        LazyFrame with added lag and rolling features.
    """
    over_cols = ["outlet_id", "item_code"]
    
    lf = lf.with_columns([
        pl.col("net_quantity").log1p().shift(1).over(over_cols).alias("lag_qty_1m"),
        pl.col("net_quantity").log1p().shift(2).over(over_cols).alias("lag_qty_2m"),
        pl.col("net_quantity").log1p().shift(3).over(over_cols).alias("lag_qty_3m"),
        pl.col("net_quantity").log1p().shift(6).over(over_cols).alias("lag_qty_6m"),
        pl.col("net_quantity").log1p().shift(12).over(over_cols).alias("lag_qty_12m"),
        
        pl.col("net_sales").log1p().shift(1).over(over_cols).alias("lag_sales_1m"),
        pl.col("net_sales").log1p().shift(2).over(over_cols).alias("lag_sales_2m"),
        pl.col("net_sales").log1p().shift(3).over(over_cols).alias("lag_sales_3m"),
        pl.col("net_sales").log1p().shift(6).over(over_cols).alias("lag_sales_6m"),
        pl.col("net_sales").log1p().shift(12).over(over_cols).alias("lag_sales_12m"),
        
        pl.col("net_quantity").rolling_mean(3, min_periods=1).over(over_cols).alias("roll_mean_qty_3m"),
        pl.col("net_quantity").rolling_mean(6, min_periods=1).over(over_cols).alias("roll_mean_qty_6m"),
        pl.col("net_quantity").rolling_mean(12, min_periods=1).over(over_cols).alias("roll_mean_qty_12m"),
        
        pl.col("net_quantity").rolling_std(3, min_periods=2).over(over_cols).alias("roll_std_qty_3m"),
        pl.col("net_quantity").rolling_std(6, min_periods=2).over(over_cols).alias("roll_std_qty_6m"),
        pl.col("net_quantity").rolling_std(12, min_periods=2).over(over_cols).alias("roll_std_qty_12m"),
        
        pl.col("net_sales").rolling_mean(3, min_periods=1).over(over_cols).alias("roll_mean_sales_3m"),
        pl.col("net_sales").rolling_mean(6, min_periods=1).over(over_cols).alias("roll_mean_sales_6m"),
        pl.col("net_sales").rolling_mean(12, min_periods=1).over(over_cols).alias("roll_mean_sales_12m"),
        pl.col("net_sales").rolling_std(6, min_periods=2).over(over_cols).alias("roll_std_sales_6m"),
        
        (pl.col("net_quantity") > 0).cast(pl.Int32).rolling_sum(3, min_periods=1).over(over_cols).alias("roll_nonzero_count_3m"),
        (pl.col("net_quantity") > 0).cast(pl.Int32).rolling_sum(6, min_periods=1).over(over_cols).alias("roll_nonzero_count_6m"),
        (pl.col("net_quantity") > 0).cast(pl.Int32).rolling_sum(12, min_periods=1).over(over_cols).alias("roll_nonzero_count_12m"),
        
        pl.col("return_quantity").rolling_sum(3, min_periods=1).over(over_cols).alias("_ret_sum_3m"),
        (pl.col("gross_quantity") + pl.col("return_quantity")).rolling_sum(3, min_periods=1).over(over_cols).alias("_gross_ret_sum_3m"),
        pl.col("return_quantity").rolling_sum(6, min_periods=1).over(over_cols).alias("_ret_sum_6m"),
        (pl.col("gross_quantity") + pl.col("return_quantity")).rolling_sum(6, min_periods=1).over(over_cols).alias("_gross_ret_sum_6m"),
    ])
    
    return lf.with_columns([
        (pl.col("roll_std_qty_3m") / (pl.col("roll_mean_qty_3m") + 1e-8)).alias("roll_cv_qty_3m"),
        (pl.col("roll_std_qty_6m") / (pl.col("roll_mean_qty_6m") + 1e-8)).alias("roll_cv_qty_6m"),
        (pl.col("roll_std_qty_12m") / (pl.col("roll_mean_qty_12m") + 1e-8)).alias("roll_cv_qty_12m"),
        
        ((pl.col("net_quantity") - pl.col("net_quantity").shift(12).over(over_cols)) / (pl.col("net_quantity").shift(12).over(over_cols) + 1e-8)).alias("yoy_growth"),
        (pl.col("roll_mean_qty_3m") / (pl.col("roll_mean_qty_6m") + 1e-8)).alias("momentum_ratio"),
        (pl.col("roll_mean_qty_3m") / (pl.col("roll_mean_qty_12m") + 1e-8)).alias("short_long_ratio"),
        
        ((pl.col("net_quantity").shift(1).over(over_cols) - pl.col("net_quantity").shift(6).over(over_cols)) / 5.0).alias("trend_slope_approx"),
        
        (pl.col("return_quantity") / (pl.col("gross_quantity") + pl.col("return_quantity") + 1e-8)).alias("current_return_rate"),
        (pl.col("_ret_sum_3m") / (pl.col("_gross_ret_sum_3m") + 1e-8)).alias("roll_return_rate_3m"),
        (pl.col("_ret_sum_6m") / (pl.col("_gross_ret_sum_6m") + 1e-8)).alias("roll_return_rate_6m"),
        
        (pl.col("net_sales") / pl.col("net_quantity").clip(lower_bound=1)).alias("price_per_unit")
    ]).drop(["_ret_sum_3m", "_gross_ret_sum_3m", "_ret_sum_6m", "_gross_ret_sum_6m"])


def build_zero_inflation_features(lf: pl.LazyFrame, save_path: str = None) -> pl.LazyFrame:
    """Build zero inflation features requiring sequential processing.
    
    Args:
        lf: LazyFrame with base data.
        save_path: Optional path to save intermediate zero-inflation features to prevent OOM.
        
    Returns:
        LazyFrame with zero inflation features.
    """
    # Select only essential columns to save memory during .collect()
    # M-Series Optimization: Use streaming=True to process out-of-core
    zero_inf_lf = lf.select(["outlet_id", "item_code", "year_month", "net_quantity"])
    df = zero_inf_lf.collect(streaming=True)
    
    over_cols = ["outlet_id", "item_code"]
    
    df = df.with_columns([
        (pl.col("outlet_id").cum_count().over(over_cols) - 1).alias("_grp_idx"),
        (pl.col("net_quantity") > 0).cast(pl.Int32).alias("_is_event")
    ])
    
    df = df.with_columns([
        pl.when(pl.col("_is_event") == 1).then(pl.col("_grp_idx")).otherwise(None)
        .forward_fill().over(over_cols).alias("_last_event_idx"),
        pl.col("_is_event").cum_sum().over(over_cols).alias("_event_cumsum")
    ])
    
    df = df.with_columns([
        (pl.col("_grp_idx") - pl.col("_last_event_idx")).alias("months_since_last_purchase"),
        (pl.col("outlet_id").cum_count().over(["outlet_id", "item_code", "_event_cumsum"]) - 1).alias("_pos_in_run"),
        pl.col("_is_event").cast(pl.Float64).rolling_mean(6, min_periods=1).over(over_cols).alias("demand_event_rate_6m"),
        pl.col("_is_event").cast(pl.Float64).rolling_mean(12, min_periods=1).over(over_cols).alias("demand_event_rate_12m")
    ])
    
    df = df.with_columns(
        pl.when(pl.col("net_quantity") == 0).then(pl.col("_pos_in_run")).otherwise(0).alias("consecutive_zeros")
    )
    
    new_features = df.select([
        "outlet_id", "item_code", "year_month",
        "months_since_last_purchase", "consecutive_zeros",
        "demand_event_rate_6m", "demand_event_rate_12m"
    ])
    
    if save_path:
        new_features.write_parquet(save_path, compression="zstd")
        new_features_lf = pl.scan_parquet(save_path)
    else:
        new_features_lf = new_features.lazy()
    
    return new_features_lf


def build_join_features(lf: pl.LazyFrame, outlet_df: pl.DataFrame, sku_df: pl.DataFrame, 
                        seasonal_df: pl.DataFrame, cat_return_rates: Dict[str, float]) -> pl.LazyFrame:
    """Join all lookup features and create interactions.
    
    Args:
        lf: Main LazyFrame.
        outlet_df: Outlet features DataFrame.
        sku_df: SKU features DataFrame.
        seasonal_df: Seasonal index DataFrame.
        cat_return_rates: Dictionary of category return rates.
        
    Returns:
        LazyFrame enriched with joins and interactions.
    """
    drop_outlet_cols = [c for c in outlet_df.columns if c in ["territory_id", "region", "province"]]
    outlet_df = outlet_df.drop(drop_outlet_cols)
    
    rename_map = {c: f"outlet_{c}" for c in outlet_df.columns if c != "outlet_id" and c != "total_net_sales"}
    outlet_df = outlet_df.with_columns(
        pl.col("total_net_sales").log1p().alias("outlet_total_net_sales_log")
    ).rename(rename_map).drop("total_net_sales")
    
    # Isolate keys and the columns required to compute the interactions
    lf_sub = lf.select(["outlet_id", "item_code", "year_month", "product_category", "roll_mean_sales_3m", "roll_mean_qty_3m"])
    
    lf_sub = (
        lf_sub.join(outlet_df.lazy(), on="outlet_id", how="left")
        .join(sku_df.lazy(), on="item_code", how="left")
        .join(seasonal_df.lazy(), on=["item_code", "month_int"], how="left")
    )
    
    lf_sub = lf_sub.with_columns(
        pl.col("cluster_definition").replace({"Power": 0, "High-Value Active": 1, "Low-Value Sporadic": 2}).cast(pl.Int8).alias("cluster_encoded"),
        (pl.col("cluster_definition") == "Power").cast(pl.Int8).alias("is_power_outlet"),
        (pl.col("cluster_definition") == "High-Value Active").cast(pl.Int8).alias("is_high_value_active"),
        (pl.col("cluster_definition") == "Low-Value Sporadic").cast(pl.Int8).alias("is_low_value_sporadic")
    )
    
    when_expr = pl.when(pl.col("product_category") == "invalid").then(0.0)
    for cat, rate in cat_return_rates.items():
        when_expr = when_expr.when(pl.col("product_category") == cat).then(rate)
    lf_sub = lf_sub.with_columns(when_expr.otherwise(0.0).alias("category_return_rate"))
    
    lf_sub = lf_sub.with_columns([
        (pl.col("cluster_encoded").cast(pl.Int32) * 3 + pl.col("demand_class_encoded").cast(pl.Int32)).cast(pl.Int8).alias("grid_cell"),
        (pl.col("roll_mean_sales_3m") / (pl.col("roll_mean_qty_3m") + 1e-8)).alias("price_per_unit_roll_3m")
    ])
    
    # Drop the temporary columns used for interaction derivations
    return lf_sub.drop(["product_category", "roll_mean_sales_3m", "roll_mean_qty_3m"])


def build_target(lf: pl.LazyFrame, horizon: int = 2) -> pl.LazyFrame:
    """Build target variables.
    
    Args:
        lf: Main LazyFrame.
        horizon: Forecast horizon in months.
        
    Returns:
        LazyFrame with target variables added.
    """
    # Isolate keys and required source columns
    lf_sub = lf.select(["outlet_id", "item_code", "year_month", "net_quantity", "net_sales"])
    
    over_cols = ["outlet_id", "item_code"]
    
    lf_sub = lf_sub.with_columns(
        pl.col("net_quantity").shift(-horizon).over(over_cols).alias("target_qty_raw")
    )
    
    lf_sub = lf_sub.with_columns([
        pl.col("target_qty_raw").log1p().alias("target_qty_log1p"),
        (pl.col("target_qty_raw") > 0).cast(pl.Int8).alias("target_is_nonzero"),
        pl.col("net_sales").log1p().shift(-horizon).over(over_cols).alias("target_log1p_net_sales")
    ])
    
    return lf_sub.select(["outlet_id", "item_code", "year_month", "target_qty_raw", "target_qty_log1p", "target_is_nonzero", "target_log1p_net_sales"])
