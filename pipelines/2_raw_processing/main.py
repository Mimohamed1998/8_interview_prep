"""Raw processing pipeline: reads CSV inputs, applies transforms, writes parquet outputs."""

import logging
import os
import sys
from pathlib import Path

# Allow running from project root: python pipelines/2_raw_processing/main.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd

from src.common.utils.config import load_config
from src.common.data_utils import read_csv, write_parquet
from src.utlits.raw_processing import process_sales, process_product, process_region


def process_all(conf: dict) -> tuple:
    """Read raw CSVs and apply all dataset-specific transforms.

    Args:
        conf: Full configuration dictionary loaded from conf.yml.

    Returns:
        Tuple of (sales_df, product_df, region_df) as processed DataFrames.
    """
    raw_path = conf["data"]["raw_path"]
    files = conf["raw_processing"]["files"]

    logger = logging.getLogger(__name__)

    logger.info("Reading sales CSV")
    sales_df = read_csv(os.path.join(raw_path, files["sales"]))
    logger.info("Processing sales — %d rows", len(sales_df))
    sales_df = process_sales(sales_df, conf)

    logger.info("Reading product CSV")
    product_df = read_csv(os.path.join(raw_path, files["product"]))
    logger.info("Processing product — %d rows", len(product_df))
    product_df = process_product(product_df, conf)

    logger.info("Reading region CSV")
    region_df = read_csv(os.path.join(raw_path, files["region"]))
    logger.info("Processing region — %d rows", len(region_df))
    region_df = process_region(region_df, conf)

    return sales_df, product_df, region_df


def main() -> None:
    """Load config, run all transforms, and write processed parquet files."""
    conf = load_config()

    log_level = conf.get("logging", {}).get("level", "INFO")
    log_format = conf.get("logging", {}).get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.basicConfig(level=getattr(logging, log_level), format=log_format)
    logger = logging.getLogger(__name__)

    logger.info("Starting raw processing pipeline")

    sales_df, product_df, region_df = process_all(conf)

    processed_path = conf["data"]["processed_path"]

    sales_out = os.path.join(processed_path, "sales.parquet")
    logger.info("Writing sales parquet → %s", sales_out)
    write_parquet(sales_df, sales_out)

    product_out = os.path.join(processed_path, "product.parquet")
    logger.info("Writing product parquet → %s", product_out)
    write_parquet(product_df, product_out)

    region_out = os.path.join(processed_path, "region.parquet")
    logger.info("Writing region parquet → %s", region_out)
    write_parquet(region_df, region_out)

    logger.info("Raw processing pipeline complete")


if __name__ == "__main__":
    main()
