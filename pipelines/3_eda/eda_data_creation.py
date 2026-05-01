"""EDA data creation pipeline: reads processed parquets, creates intermediate datasets."""

import logging
import os
import sys
from pathlib import Path

# Allow running from project root: python pipelines/3_eda/eda_data_creation.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd

from src.common.utils.config import load_config
from src.common.data_utils import read_parquet, write_parquet
from src.utlits.raw_processing import (
    create_base_sales_enriched,
    create_outlet_sku_monthly_demand,
    create_outlet_monthly_activity,
    create_monthly_territory_demand,
    create_outlet_features,
)


def create_datasets(conf: dict) -> dict:
    """Create all intermediate datasets for EDA.

    Args:
        conf: Full configuration dictionary loaded from conf.yml.

    Returns:
        Dictionary of dataset names to DataFrames.
    """
    processed_path = conf["data"]["processed_path"]

    sales_df = read_parquet(os.path.join(processed_path, "sales.parquet"))
    product_df = read_parquet(os.path.join(processed_path, "product.parquet"))
    region_df = read_parquet(os.path.join(processed_path, "region.parquet"))

    base_sales_enriched = create_base_sales_enriched(sales_df, product_df, region_df)
    logger = logging.getLogger(__name__)
    logger.info(f"Created base_sales_enriched: {len(base_sales_enriched)} rows")

    outlet_sku_monthly_demand = create_outlet_sku_monthly_demand(base_sales_enriched)
    logger.info(f"Created outlet_sku_monthly_demand: {len(outlet_sku_monthly_demand)} rows")

    outlet_monthly_activity = create_outlet_monthly_activity(base_sales_enriched)
    logger.info(f"Created outlet_monthly_activity: {len(outlet_monthly_activity)} rows")

    monthly_territory_demand = create_monthly_territory_demand(outlet_sku_monthly_demand, region_df)
    logger.info(f"Created monthly_territory_demand: {len(monthly_territory_demand)} rows")

    outlet_features = create_outlet_features(outlet_monthly_activity)
    logger.info(f"Created outlet_features: {len(outlet_features)} rows")

    return {
        "base_sales_enriched": base_sales_enriched,
        "outlet_sku_monthly_demand": outlet_sku_monthly_demand,
        "outlet_monthly_activity": outlet_monthly_activity,
        "monthly_territory_demand": monthly_territory_demand,
        "outlet_features": outlet_features,
    }


def main() -> None:
    """Load config, create all datasets, and write intermediate parquet files."""
    conf = load_config()

    log_level = conf.get("logging", {}).get("level", "INFO")
    log_format = conf.get("logging", {}).get(
        "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logging.basicConfig(level=getattr(logging, log_level), format=log_format)
    logger = logging.getLogger(__name__)

    logger.info("Starting EDA data creation pipeline")

    datasets = create_datasets(conf)

    intermediate_path = conf["data"]["intermediate_path"]

    for name, df in datasets.items():
        out_path = os.path.join(intermediate_path, f"{name}.parquet")
        logger.info(f"Writing {name} parquet → {out_path}")
        write_parquet(df, out_path)

    logger.info("EDA data creation pipeline complete")


if __name__ == "__main__":
    main()