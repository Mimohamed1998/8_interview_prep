"""Create outlet_monthly_activity — reads base_sales_enriched from intermediate. Uses Polars."""

import logging
import os
import sys
from datetime import date as Date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import polars as pl

from src.common.utils.config import load_config


def _build(base: pl.DataFrame) -> pl.DataFrame:
    min_ym = base["year_month"].min()
    max_ym = base["year_month"].max()
    months = (
        pl.date_range(Date.fromisoformat(min_ym + "-01"), Date.fromisoformat(max_ym + "-01"), interval="1mo", eager=True)
        .dt.strftime("%Y-%m")
        .to_list()
    )

    full_grid = base.select("outlet_id").unique().join(pl.DataFrame({"year_month": months}), how="cross")

    # Most frequent non-null payment_term per outlet per month
    payment_mode = (
        base.filter(pl.col("payment_term").is_not_null())
        .group_by(["outlet_id", "year_month", "payment_term"])
        .agg(pl.len().alias("cnt"))
        .sort(["outlet_id", "year_month", "cnt"], descending=[False, False, True])
        .group_by(["outlet_id", "year_month"], maintain_order=True)
        .first()
        .select(["outlet_id", "year_month", pl.col("payment_term").alias("primary_payment_term")])
    )

    agg = (
        base.group_by(["outlet_id", "year_month"]).agg(
            (pl.col("document_type") == "invoice").sum().alias("n_invoices"),
            pl.when(pl.col("quantity") > 0).then(pl.col("quantity")).otherwise(0).sum().alias("gross_quantity"),
            pl.when(pl.col("quantity") > 0).then(pl.col("net_sales")).otherwise(0).sum().alias("gross_sales"),
            (pl.col("document_type") == "return").sum().alias("n_returns"),
            pl.when(pl.col("quantity") < 0).then(pl.col("quantity").abs()).otherwise(0).sum().alias("return_quantity"),
            pl.when(pl.col("quantity") < 0).then(pl.col("net_sales").abs()).otherwise(0).sum().alias("return_sales"),
            pl.col("item_code").n_unique().alias("n_unique_skus"),
            pl.col("product_category").n_unique().alias("n_unique_categories"),
        )
        .join(payment_mode, on=["outlet_id", "year_month"], how="left")
    )

    numeric_cols = ["n_invoices", "gross_quantity", "gross_sales", "n_returns",
                    "return_quantity", "return_sales", "n_unique_skus", "n_unique_categories"]
    df = (
        full_grid.join(agg, on=["outlet_id", "year_month"], how="left")
        .with_columns(
            [pl.col(c).fill_null(0) for c in numeric_cols]
            + [pl.col("primary_payment_term").fill_null("unknown")]
        )
    )

    dims = (
        base.select(["outlet_id", "territory_id", "region", "district", "province"])
        .unique(subset=["outlet_id"])
    )
    return df.join(dims, on="outlet_id", how="left")


def main() -> None:
    conf = load_config()
    logging.basicConfig(
        level=getattr(logging, conf.get("logging", {}).get("level", "INFO")),
        format=conf.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    )
    logger = logging.getLogger(__name__)

    intermediate_path = conf["data"]["intermediate_path"]

    logger.info("Reading base_sales_enriched from intermediate")
    base = pl.read_parquet(os.path.join(intermediate_path, "base_sales_enriched.parquet"))

    df = _build(base)
    logger.info(f"outlet_monthly_activity: {len(df)} rows")

    out_path = os.path.join(intermediate_path, "outlet_monthly_activity.parquet")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out_path)
    logger.info(f"Written → {out_path}")


if __name__ == "__main__":
    main()
