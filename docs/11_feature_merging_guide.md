# Data Merging Documentation for Demand Intelligence Pipeline

This document outlines how to merge the separately generated feature datasets back into a single training matrix for XGBoost modeling. 

To optimize memory usage and processing speed on local machines (like Apple Silicon), the feature engineering pipeline has been modularized to output several distinct datasets instead of one monolithic table.

## Intermediate Datasets

All datasets are saved in `data/Intermediate/`. The main time-series datasets share the identical primary keys: `["outlet_id", "item_code", "year_month"]`. Lookup tables can be joined on their respective keys.

1. **`base_features_for_modeling.parquet`**: Contains the core demand, time, lag, and rolling window features.
2. **`zero_inflation_features.parquet`**: Contains Croston-style zero-inflation and inter-arrival features.
3. **`target_features.parquet`**: Contains the shifted target variables for prediction (`target_qty_log1p`, etc.).
4. **`enriched_sku_lookup.parquet`**: Contains static SKU traits, demand class encodings, and aggregated item activity features.
5. **`seasonal_index_lookup.parquet`**: Contains seasonal indices calculated per `item_code` and `month_int`.

---

## How to Merge for Training

Because the main datasets share the exact same primary keys and are sorted identically during generation, joining them together is highly efficient. The lookup tables can be joined on their respective identifiers.

When loading the data for model training, use Polars' `scan_parquet` to lazily join the tables. This allows Polars' query optimizer to only load the specific columns you need for the current model grid cell.

### Python Example

```python
import polars as pl
from pathlib import Path

def load_training_matrix(intermediate_dir: str) -> pl.LazyFrame:
    """Lazily joins all feature datasets into a single modeling matrix."""
    
    int_dir = Path(intermediate_dir)
    
    # 1. Start with the base features
    lf_base = pl.scan_parquet(int_dir / "base_features_for_modeling.parquet")
    
    # 2. Lazy scan the components
    lf_zero = pl.scan_parquet(int_dir / "zero_inflation_features.parquet")
    lf_target = pl.scan_parquet(int_dir / "target_features.parquet")
    
    # 3. Lazy scan the lookup tables
    lf_sku = pl.scan_parquet(int_dir / "enriched_sku_lookup.parquet")
    lf_seasonal = pl.scan_parquet(int_dir / "seasonal_index_lookup.parquet")
    
    # 4. Join the main datasets on primary keys
    join_keys = ["outlet_id", "item_code", "year_month"]
    
    modeling_matrix = (
        lf_base
        .join(lf_zero, on=join_keys, how="left")
        .join(lf_target, on=join_keys, how="left")
    )
    
    # 5. Join lookup tables
    modeling_matrix = (
        modeling_matrix
        .join(lf_sku, on="item_code", how="left")
        .join(lf_seasonal, on=["item_code", "month_int"], how="left")
    )
    
    return modeling_matrix

# Usage during modeling:
# modeling_lf = load_training_matrix("data/Intermediate")
#
# # Filter to a specific model cell (e.g., Power Cluster)
# cell_0_data = modeling_lf.filter(pl.col("cluster_definition") == "Power").collect()
```

### Memory Optimization Tips

- **Column Selection**: If a specific XGBoost model (like Continuous demand) doesn't need zero-inflation features, you can simply omit `lf_zero` from the join chain, saving RAM.
- **Drop Churned**: The pipeline already excludes churned outlets. If you need to filter further, apply `.filter()` to `lf_base` *before* the joins. Polars will push this filter down and avoid loading rows from the joined tables!
