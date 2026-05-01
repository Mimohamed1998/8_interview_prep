"""Create monthly_territory_demand — reads outlet_sku_monthly_demand + region. Uses Polars."""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import polars as pl

from src.common.utils.config import load_config


def _build(outlet_sku: pl.DataFrame, region: pl.DataFrame) -> pl.DataFrame:
    months = outlet_sku["year_month"].unique().sort().to_list()
    full_grid = region.select("territory_id").unique().join(pl.DataFrame({"year_month": months}), how="cross")

    agg = outlet_sku.group_by(["year_month", "territory_id"]).agg(
        pl.col("net_quantity").sum(),
        pl.col("net_sales").sum(),
        pl.col("gross_quantity").sum(),
        pl.col("gross_sales").sum(),
        pl.col("return_quantity").sum(),
        pl.col("return_sales").sum(),
        (pl.col("n_invoices") > 0).sum().alias("n_unique_skus"),
    )

    numeric_cols = ["net_quantity", "net_sales", "gross_quantity", "gross_sales",
                    "return_quantity", "return_sales", "n_unique_skus"]
    df = (
        full_grid.join(agg, on=["territory_id", "year_month"], how="left")
        .with_columns([pl.col(c).fill_null(0) for c in numeric_cols])
    )
    return df.join(region, on="territory_id", how="left")


def main() -> None:
    conf = load_config()
    logging.basicConfig(
        level=getattr(logging, conf.get("logging", {}).get("level", "INFO")),
        format=conf.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    )
    logger = logging.getLogger(__name__)

    processed_path    = conf["data"]["processed_path"]
    intermediate_path = conf["data"]["intermediate_path"]

    logger.info("Reading outlet_sku_monthly_demand from intermediate")
    outlet_sku = pl.read_parquet(os.path.join(intermediate_path, "outlet_sku_monthly_demand.parquet"))

    logger.info("Reading region from processed")
    region = pl.read_parquet(os.path.join(processed_path, "region.parquet"))

    df = _build(outlet_sku, region)
    logger.info(f"monthly_territory_demand: {len(df)} rows")

    out_path = os.path.join(intermediate_path, "monthly_territory_demand.parquet")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out_path)
    logger.info(f"Written → {out_path}")


if __name__ == "__main__":
    main()
