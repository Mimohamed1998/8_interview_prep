import os
from pathlib import Path
import polars as pl
import pandas as pd

def main():
    print("Loading data...")
    # Load intermediate data
    df_demand = pl.read_parquet("data/intermediate/outlet_sku_monthly_demand.parquet")
    df_item_class = pl.read_parquet("data/output/m3_sku_demand_continuity.parquet")

    print("Aggregating to item-month level...")
    # Aggregate to item-month grain
    df_item_month = df_demand.group_by(["item_code", "year_month", "product_category", "product_line", "brand"]).agg([
        pl.col("net_quantity").sum().alias("target_qty_raw"),
        pl.col("net_sales").sum(),
        pl.col("gross_quantity").sum(),
        pl.col("gross_sales").sum(),
        pl.col("return_quantity").sum(),
        pl.col("return_sales").sum(),
        pl.col("n_invoices").sum(),
        pl.col("n_returns").sum(),
    ])

    print("Adding temporal features...")
    # Add year and month_int
    df_item_month = df_item_month.with_columns([
        pl.col("year_month").str.slice(0, 4).cast(pl.Int32).alias("year"),
        pl.col("year_month").str.slice(5, 2).cast(pl.Int32).alias("month_int")
    ])

    # Sort to ensure proper lag/rolling computation
    df_item_month = df_item_month.sort(["item_code", "year_month"])

    print("Computing lags and rolling features...")
    # Create temporal features per item
    df_item_month = df_item_month.with_columns([
        pl.col("target_qty_raw").shift(1).over("item_code").alias("lag_qty_1m"),
        pl.col("target_qty_raw").shift(2).over("item_code").alias("lag_qty_2m"),
        pl.col("target_qty_raw").shift(3).over("item_code").alias("lag_qty_3m"),
        pl.col("target_qty_raw").shift(6).over("item_code").alias("lag_qty_6m"),
        pl.col("target_qty_raw").shift(12).over("item_code").alias("lag_qty_12m"),

        pl.col("target_qty_raw").rolling_mean(window_size=3).over("item_code").alias("roll_mean_qty_3m"),
        pl.col("target_qty_raw").rolling_mean(window_size=12).over("item_code").alias("roll_mean_qty_12m"),
        pl.col("target_qty_raw").rolling_std(window_size=12).over("item_code").alias("roll_std_qty_12m"),
        
        pl.col("net_sales").rolling_mean(window_size=3).over("item_code").alias("roll_mean_sales_3m"),
        pl.col("net_sales").rolling_mean(window_size=12).over("item_code").alias("roll_mean_sales_12m"),
    ])

    print("Joining item classification...")
    # Join with item classification to get demand_class
    df_final = df_item_month.join(
        df_item_class.select(["item_code", "demand_class", "activity_rate", "cv"]),
        on="item_code",
        how="left"
    )

    # Fill nulls in lag/rolling features
    df_final = df_final.fill_null(0)
    
    # Save the aggregated output
    output_path = "data/intermediate/item_monthly_modeling_matrix.parquet"
    print(f"Saving to {output_path}...")
    df_final.write_parquet(output_path)
    print(f"Rows: {df_final.shape[0]} | Columns: {df_final.shape[1]}")
    print("Done!")

if __name__ == "__main__":
    main()
