"""
Pipeline script to generate feature engineering dataset.
"""

import sys
import logging
import polars as pl
from pathlib import Path

# Add the root directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.common.utils.config import load_config
from src.common.data_utils import read_parquet, write_parquet
from src.feature_engineering.feature_engineering import (
    build_seasonal_index,
    build_enriched_sku_features,
    build_territory_context,
    build_base_lazy,
    build_time_features,
    build_lag_rolling_features,
    build_zero_inflation_features,
    build_join_features,
    build_target
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_feature_engineering() -> None:
    """Run the feature engineering pipeline and write output."""
    logger.info("Starting feature engineering process.")
    
    # M-Series Optimization: Enable global string cache for memory-efficient joins
    pl.enable_string_cache()
    
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    data_dir = base_dir / "data"
    int_dir = data_dir / "Intermediate"
    out_dir = data_dir / "output"
    
    demand_path = str(int_dir / "outlet_sku_monthly_demand.parquet")
    item_class_path = str(int_dir / "item_classification.parquet")
    cluster_path = str(int_dir / "outlet_cluster_definitions.parquet")
    outlet_features_path = str(int_dir / "outlet_features.parquet")
    territory_path = str(int_dir / "monthly_territory_demand.parquet")
    sku_continuity_path = str(out_dir / "m3_sku_demand_continuity.parquet")
    output_path = str(int_dir / "feature_engineering.parquet")
    
    try:
        config = load_config()
        fe_config = config.get("feature_engineering", {})
        training_start = fe_config.get("training_window", {}).get("start", "2015-01")
        training_end = fe_config.get("training_window", {}).get("end", "2019-12")
        horizon = fe_config.get("target_horizon", 2)
        cat_return_rates = fe_config.get("category_return_rates", {
            "cat_2": 0.1180, "cat_3": 0.0916, "cat_4": 0.0832, 
            "cat_5": 0.0664, "cat_6": 0.0787, "cat_7": 0.0687
        })
    except Exception:
        training_start = "2015-01"
        training_end = "2019-12"
        horizon = 2
        cat_return_rates = {
            "Cat_2": 0.1180, "Cat_3": 0.0916, "Cat_4": 0.0832, 
            "Cat_5": 0.0664, "Cat_6": 0.0787, "Cat_7": 0.0687
        }

    logger.info("Reading lookup tables using data_utils")
    item_class_df = pl.from_pandas(read_parquet(item_class_path))
    cluster_df = pl.from_pandas(read_parquet(cluster_path))
    outlet_features_df = pl.from_pandas(read_parquet(outlet_features_path))
    territory_df = pl.from_pandas(read_parquet(territory_path))
    sku_continuity_df = pl.from_pandas(read_parquet(sku_continuity_path))
    
    logger.info("Building lookup features")
    seasonal_df = build_seasonal_index(demand_path, training_start, training_end)
    seasonal_path = str(int_dir / "seasonal_index_lookup.parquet")
    logger.info(f"Saving seasonal index lookup to {seasonal_path}")
    seasonal_df.write_parquet(seasonal_path, compression="zstd")
    
    sku_df = build_enriched_sku_features(sku_continuity_df, item_class_df)
    sku_path = str(int_dir / "enriched_sku_lookup.parquet")
    logger.info(f"Saving enriched SKU lookup to {sku_path}")
    sku_df.write_parquet(sku_path, compression="zstd")
    # Note: we no longer build terr_df because monthly territory demand was removed per request
    
    logger.info("Building base features")
    lf_base = build_base_lazy(demand_path, cluster_df, training_start, training_end)
    lf_base = build_time_features(lf_base)
    lf_base = build_lag_rolling_features(lf_base)
    
    base_features_path = str(int_dir / "base_features_for_modeling.parquet")
    logger.info(f"Saving base features to {base_features_path} to save memory")
    lf_base.sink_parquet(base_features_path, compression="zstd")
    
    logger.info("Reading base features back")
    lf_base_scanned = pl.scan_parquet(base_features_path)
    
    logger.info("Building zero-inflation features (triggering collect)")
    zero_inf_path = str(int_dir / "zero_inflation_features.parquet")
    _ = build_zero_inflation_features(lf_base_scanned, save_path=zero_inf_path)
    
    # logger.info("Building join features")
    # lf_join = build_join_features(lf_base_scanned, outlet_features_df, sku_df, seasonal_df, cat_return_rates)
    # join_features_path = str(int_dir / "lookup_join_features.parquet")
    # logger.info(f"Writing lookup join features to {join_features_path}")
    # lf_join.sink_parquet(join_features_path, compression="zstd")
    
    # logger.info("Building target features")
    # lf_target = build_target(lf_base_scanned, horizon)
    # target_features_path = str(int_dir / "target_features.parquet")
    # logger.info(f"Writing target features to {target_features_path}")
    # lf_target.sink_parquet(target_features_path, compression="zstd")
    
    # logger.info("Successfully generated all separate feature datasets.")


def main() -> None:
    """Main execution point."""
    run_feature_engineering()


if __name__ == "__main__":
    main()
