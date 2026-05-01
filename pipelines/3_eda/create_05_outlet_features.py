"""Create outlet_features — reads outlet_monthly_activity from intermediate. Uses Polars."""

import logging
import os
import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import polars as pl

from src.common.utils.config import load_config


def _subtract_months(d: Date, n: int) -> Date:
    month = d.month - n
    year = d.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1
    return Date(year, month, 1)


def _build(activity: pl.DataFrame) -> pl.DataFrame:
    max_month_str = activity["year_month"].max()
    max_date = Date.fromisoformat(max_month_str + "-01")
    start_date = _subtract_months(max_date, 11)

    window_months = (
        pl.date_range(start_date, max_date, interval="1mo", eager=True)
        .dt.strftime("%Y-%m")
        .to_list()
    )
    window_df = activity.filter(pl.col("year_month").is_in(window_months))

    # Momentum: sum(last 3 months gross_sales) / sum(first 9 months gross_sales)
    ranked = window_df.sort(["outlet_id", "year_month"]).with_columns([
        pl.col("year_month").rank("ordinal").over("outlet_id").cast(pl.Int64).alias("_rank"),
        pl.len().over("outlet_id").cast(pl.Int64).alias("_n"),
    ])
    last3 = (
        ranked.filter(pl.col("_rank") > pl.col("_n") - 3)
        .group_by("outlet_id")
        .agg(pl.col("gross_sales").sum().alias("_last3"))
    )
    first_n3 = (
        ranked.filter(pl.col("_rank") <= pl.col("_n") - 3)
        .group_by("outlet_id")
        .agg(pl.col("gross_sales").sum().alias("_first_n3"))
    )
    n_df = ranked.group_by("outlet_id").agg(pl.col("_n").first())

    momentum_df = (
        last3.join(first_n3, on="outlet_id", how="left")
        .join(n_df, on="outlet_id", how="left")
        .with_columns([pl.col("_last3").fill_null(0), pl.col("_first_n3").fill_null(0)])
        .with_columns(
            pl.when((pl.col("_n") >= 6) & (pl.col("_first_n3") > 0))
            .then(pl.col("_last3") / pl.col("_first_n3"))
            .otherwise(pl.lit(0.0))
            .alias("momentum")
        )
        .select(["outlet_id", "momentum"])
    )

    # Main per-outlet aggregations over the 12-month window
    features = window_df.group_by("outlet_id").agg(
        pl.col("gross_sales").sum().alias("total_net_sales"),
        pl.col("gross_quantity").sum().alias("total_quantity"),
        (pl.col("n_invoices") > 0).sum().alias("active_months"),
        ((pl.col("n_invoices") > 0).sum().cast(pl.Float64) / 12).alias("loyalty_ratio"),
        (pl.col("n_invoices").sum().cast(pl.Float64) /
         (pl.col("n_invoices") > 0).sum().cast(pl.Float64)).fill_nan(0.0).alias("avg_txn_per_active_month"),
        (pl.col("gross_sales").sum() /
         (pl.col("gross_sales") > 0).sum().cast(pl.Float64)).fill_nan(0.0).alias("avg_net_sales_per_txn"),
        (pl.col("gross_quantity").sum() /
         (pl.col("gross_quantity") > 0).sum().cast(pl.Float64)).fill_nan(0.0).alias("avg_qty_per_txn"),
        pl.col("n_unique_skus").max(),
        pl.col("n_unique_categories").max(),
        (pl.col("n_returns").sum().cast(pl.Float64) /
         ((pl.col("n_returns") > 0).sum() + pl.col("n_returns").sum()).cast(pl.Float64))
            .fill_nan(0.0).alias("return_rate"),
        pl.lit(0).cast(pl.Int64).alias("recency_months"),
        ((pl.col("primary_payment_term") == "cash").sum().cast(pl.Float64) /
         pl.len().cast(pl.Float64)).fill_nan(0.0).alias("pct_cash_txn"),
    )

    features = (
        features
        .join(momentum_df, on="outlet_id", how="left")
        .with_columns(pl.col("momentum").fill_null(0.0))
        .with_columns((pl.col("active_months") >= 1).alias("is_active"))
    )

    dims = (
        activity.select(["outlet_id", "territory_id", "region", "province"])
        .unique(subset=["outlet_id"])
    )
    return features.join(dims, on="outlet_id", how="left")


def main() -> None:
    conf = load_config()
    logging.basicConfig(
        level=getattr(logging, conf.get("logging", {}).get("level", "INFO")),
        format=conf.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    )
    logger = logging.getLogger(__name__)

    intermediate_path = conf["data"]["intermediate_path"]

    logger.info("Reading outlet_monthly_activity from intermediate")
    activity = pl.read_parquet(os.path.join(intermediate_path, "outlet_monthly_activity.parquet"))

    df = _build(activity)
    logger.info(f"outlet_features: {len(df)} rows")

    out_path = os.path.join(intermediate_path, "outlet_features.parquet")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out_path)
    logger.info(f"Written → {out_path}")


if __name__ == "__main__":
    main()
