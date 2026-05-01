"""
Core logic for SKU demand-class classification.

All functions accept thresholds and flags as explicit parameters sourced from
conf/conf.yml so there are no hardcoded values in this module.
"""

import polars as pl

MODEL_FAMILY = {
    "Continuous":   "SARIMA(p,1,q)(P,1,Q)_12 or ETS(A,A,A)",
    "Intermittent": "Croston / SBA on deseasonalised demand",
    "Lumpy":        "ADIDA + manual threshold override",
}

EVAL_METRIC = {
    "Continuous":   "RMSE, MAPE (log scale), coverage probability",
    "Intermittent": "MASE, PIS (Periods in Stock), service-level simulation",
    "Lumpy":        "MASE, PIS (Periods in Stock), service-level simulation",
}

SEASONAL_TREATMENT = {
    "Continuous":   "SARIMA seasonal order (P,1,Q)_12; d=1 (ADF/KPSS confirmed)",
    "Intermittent": "Pre-deseasonalise with M2 national seasonal index; re-apply post-forecast",
    "Lumpy":        "Aggregate to annual/bi-annual via ADIDA; disaggregate with M2 seasonal index",
}

LOG_TRANSFORM = {
    "Continuous":   "Optional at national level; mandatory at outlet-SKU grain (skewness 38x)",
    "Intermittent": "Not applicable — Croston operates on intervals and sizes separately",
    "Lumpy":        "Not applicable — ADIDA aggregates before estimation",
}


def national_sku_demand(path: str) -> pl.DataFrame:
    """Aggregate outlet_sku_monthly_demand to national monthly SKU demand.

    Uses scan_parquet so the group_by is pushed down before materialising —
    avoids loading the full 123M-row file into RAM.
    All available months are used; classification is not restricted to the
    model-training window.
    """
    return (
        pl.scan_parquet(path)
        .group_by(["item_code", "year_month"])
        .agg(
            pl.col("gross_quantity").sum(),
            pl.col("gross_sales").sum(),
            pl.col("net_quantity").sum(),
            pl.col("net_sales").sum(),
            pl.col("return_quantity").sum(),
            pl.col("return_sales").sum(),
        )
        .sort(["item_code", "year_month"])
        .collect()
    )


def compute_activity_cv(national: pl.DataFrame) -> pl.DataFrame:
    """
    Compute per-SKU activity_rate and CV from national monthly demand.

    activity_rate = n_active_months / total_months  (active = gross_quantity > 0)
    cv            = std(nonzero_demand) / mean(nonzero_demand)
    """
    total_months = national.select("year_month").unique().height

    return (
        national
        .group_by("item_code")
        .agg(
            pl.col("gross_quantity").filter(pl.col("gross_quantity") > 0).count().alias("n_active_months"),
            pl.col("gross_quantity").filter(pl.col("gross_quantity") > 0).mean().alias("mean_nonzero_demand"),
            pl.col("gross_quantity").filter(pl.col("gross_quantity") > 0).std().alias("std_nonzero_demand"),
            pl.col("gross_quantity").sum().alias("total_quantity"),
            pl.col("gross_sales").sum().alias("total_gross_sales"),
            pl.col("net_sales").sum().alias("total_net_sales"),
            pl.col("return_quantity").sum().alias("total_return_quantity"),
        )
        .with_columns([
            (pl.col("n_active_months").cast(pl.Float64) / pl.lit(float(total_months))).alias("activity_rate"),
            (pl.lit(float(total_months)) / pl.col("n_active_months").cast(pl.Float64)).alias("adi"),
        ])
        .with_columns(
            pl.when(pl.col("mean_nonzero_demand") > 0)
            .then(pl.col("std_nonzero_demand") / pl.col("mean_nonzero_demand"))
            .otherwise(0.0)
            .alias("cv")
        )
        .with_columns([
            (pl.col("cv") ** 2).alias("cv2"),
            pl.lit(total_months).cast(pl.Int64).alias("total_months_in_window"),
        ])
    )


def classify(
    stats: pl.DataFrame,
    activity_continuous_min: float,
    cv_continuous_max: float,
    activity_lumpy_max: float,
    cv_lumpy_min: float,
) -> pl.DataFrame:
    """Assign demand_class and model metadata to each SKU."""
    return (
        stats
        .with_columns(
            pl.when(
                (pl.col("activity_rate") >= activity_continuous_min)
                & (pl.col("cv") < cv_continuous_max)
            ).then(pl.lit("Continuous"))
            .when(
                (pl.col("activity_rate") < activity_lumpy_max)
                | (pl.col("cv") > cv_lumpy_min)
            ).then(pl.lit("Lumpy"))
            .otherwise(pl.lit("Intermittent"))
            .alias("demand_class")
        )
        .with_columns([
            pl.col("demand_class").replace(MODEL_FAMILY).alias("model_family"),
            pl.col("demand_class").replace(EVAL_METRIC).alias("eval_metric"),
            pl.col("demand_class").replace(SEASONAL_TREATMENT).alias("seasonal_treatment"),
            pl.col("demand_class").replace(LOG_TRANSFORM).alias("log_transform_policy"),
        ])
    )


def enrich_dimensions(classified: pl.DataFrame, demand_path: str) -> pl.DataFrame:
    """Join product dimensions (category, line, brand) onto classified SKUs."""
    dims = (
        pl.scan_parquet(demand_path)
        .select(["item_code", "product_category", "product_line", "brand"])
        .unique(subset=["item_code"])
        .collect()
    )
    return classified.join(dims, on="item_code", how="left")


def add_special_flags(
    classified: pl.DataFrame,
    structural_collapse_line: str,
    hyper_growth_line: str,
) -> pl.DataFrame:
    """Tag SKUs requiring non-standard modeling treatment."""
    return classified.with_columns(
        pl.when(pl.col("product_line") == structural_collapse_line)
        .then(pl.lit("structural_collapse_trend"))
        .when(pl.col("product_line") == hyper_growth_line)
        .then(pl.lit("bass_diffusion_short_window"))
        .otherwise(pl.lit("standard"))
        .alias("modeling_flag")
    )
