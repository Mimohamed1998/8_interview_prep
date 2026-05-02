def get_feature_columns(df, target_col, drop_cfg):
    """Return the feature column list for a given model, removing forbidden and leak columns.

    Returns:
        Tuple of (feature_cols: list[str], target_col: str).
    """
    all_targets = drop_cfg["target_leakage"]
    all_drop = set(
        drop_cfg["identifiers"] +
        drop_cfg["geo_admin"] +
        drop_cfg["product_admin"] +
        drop_cfg["segment_strings"] +
        [c for c in all_targets if c != target_col]
    )
    feature_cols = [c for c in df.columns if c not in all_drop and c != target_col]
    return feature_cols, target_col
