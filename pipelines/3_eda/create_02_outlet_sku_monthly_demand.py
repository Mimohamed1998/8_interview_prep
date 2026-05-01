"""Create outlet_sku_monthly_demand — reads base_sales_enriched from intermediate. Uses Polars."""

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

    active_pairs = (
        base.filter(pl.col("document_type") == "invoice")
        .select(["outlet_id", "item_code"])
        .unique()
    )
    full_grid = active_pairs.join(pl.DataFrame({"year_month": months}), how="cross")

    agg = base.group_by(["outlet_id", "item_code", "year_month"]).agg(
        pl.col("quantity").sum().alias("net_quantity"),
        pl.col("net_sales").sum().alias("net_sales"),
        pl.when(pl.col("quantity") > 0).then(pl.col("quantity")).otherwise(0).sum().alias("gross_quantity"),
        pl.when(pl.col("quantity") > 0).then(pl.col("net_sales")).otherwise(0).sum().alias("gross_sales"),
        pl.when(pl.col("quantity") < 0).then(pl.col("quantity").abs()).otherwise(0).sum().alias("return_quantity"),
        pl.when(pl.col("quantity") < 0).then(pl.col("net_sales").abs()).otherwise(0).sum().alias("return_sales"),
        (pl.col("document_type") == "invoice").sum().alias("n_invoices"),
        (pl.col("document_type") == "return").sum().alias("n_returns"),
    )

    numeric_cols = ["net_quantity", "net_sales", "gross_quantity", "gross_sales",
                    "return_quantity", "return_sales", "n_invoices", "n_returns"]
    df = (
        full_grid.join(agg, on=["outlet_id", "item_code", "year_month"], how="left")
        .with_columns([pl.col(c).fill_null(0) for c in numeric_cols])
    )

    dims = (
        base.select(["outlet_id", "item_code", "territory_id", "region", "district",
                     "province", "product_category", "product_line", "brand"])
        .unique(subset=["outlet_id", "item_code"])
    )
    return df.join(dims, on=["outlet_id", "item_code"], how="left")


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
    logger.info(f"outlet_sku_monthly_demand: {len(df)} rows")

    out_path = os.path.join(intermediate_path, "outlet_sku_monthly_demand.parquet")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out_path)
    logger.info(f"Written → {out_path}")


if __name__ == "__main__":
    main()
