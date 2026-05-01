"""Item classification pipeline — entry point.

Reads thresholds from conf/conf.yml, delegates all logic to
src/item_classification/item_classification.py, and writes
data/output/item_classification.parquet.
"""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import polars as pl

from src.common.utils.config import load_config
from src.item_classification.item_classification import (
    add_special_flags,
    classify,
    compute_activity_cv,
    enrich_dimensions,
    national_sku_demand,
)

_COL_ORDER = [
    "item_code", "demand_class",
]


def _build(demand_path: str, conf: dict) -> pl.DataFrame:
    thresholds = conf["item_classification"]["thresholds"]
    flags      = conf["item_classification"]["special_flags"]

    national   = national_sku_demand(demand_path)
    stats      = compute_activity_cv(national)
    classified = classify(
        stats,
        activity_continuous_min=thresholds["activity_continuous_min"],
        cv_continuous_max=thresholds["cv_continuous_max"],
        activity_lumpy_max=thresholds["activity_lumpy_max"],
        cv_lumpy_min=thresholds["cv_lumpy_min"],
    )
    classified = enrich_dimensions(classified, demand_path)
    classified = add_special_flags(
        classified,
        structural_collapse_line=flags["structural_collapse"],
        hyper_growth_line=flags["hyper_growth"],
    )
    return classified.select(_COL_ORDER).sort("demand_class", "item_code")


def main() -> None:
    conf = load_config()
    logging.basicConfig(
        level=getattr(logging, conf.get("logging", {}).get("level", "INFO")),
        format=conf.get("logging", {}).get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    )
    logger = logging.getLogger(__name__)

    demand_path = os.path.join(conf["data"]["intermediate_path"], "outlet_sku_monthly_demand.parquet")
    logger.info(f"outlet_sku_monthly_demand: {demand_path}")

    df = _build(demand_path, conf)

    for row in df.group_by("demand_class").len().sort("demand_class").iter_rows(named=True):
        logger.info(f"  {row['demand_class']}: {row['len']} SKUs")

    out_path = os.path.join(conf["data"]["intermediate_path"], "item_classification.parquet")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out_path)
    logger.info(f"Written → {out_path}")


if __name__ == "__main__":
    main()
