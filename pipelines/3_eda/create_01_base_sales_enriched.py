"""Create base_sales_enriched from processed parquets."""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.common.utils.config import load_config
from src.common.data_utils import read_parquet, write_parquet
from src.utlits.raw_processing import create_base_sales_enriched


def main() -> None:
    conf = load_config()
    logging.basicConfig(
        level=getattr(logging, conf.get("logging", {}).get("level", "INFO")),
        format=conf.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    )
    logger = logging.getLogger(__name__)

    processed_path = conf["data"]["processed_path"]
    intermediate_path = conf["data"]["intermediate_path"]

    logger.info("Reading processed parquets")
    sales_df   = read_parquet(os.path.join(processed_path, "sales.parquet"))
    product_df = read_parquet(os.path.join(processed_path, "product.parquet"))
    region_df  = read_parquet(os.path.join(processed_path, "region.parquet"))

    df = create_base_sales_enriched(sales_df, product_df, region_df)
    logger.info(f"base_sales_enriched: {len(df)} rows")

    out_path = os.path.join(intermediate_path, "base_sales_enriched.parquet")
    write_parquet(df, out_path)
    logger.info(f"Written → {out_path}")


if __name__ == "__main__":
    main()
