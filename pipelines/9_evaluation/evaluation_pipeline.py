"""Cohort evaluation pipeline — per-item and per-outlet-cluster WAPE/MAPE."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.common.utils.config import load_config
from src.model_prediction_pipelines.evaluation import (
    evaluate_by_item,
    evaluate_by_outlet_cluster,
)


def main():
    cfg = load_config()
    inf_cfg = cfg["inference"]
    mod_cfg = cfg["modeling"]

    output_path = inf_cfg["output_path"]
    eval_start = mod_cfg["eval_start"]
    eval_end = mod_cfg["eval_end"]

    buffered = pd.read_parquet(f"{output_path}/predictions_buffered.parquet")
    item_meta = pd.read_parquet(f"{inf_cfg['cell_data_path']}/item_classification.parquet")
    outlet_clusters = pd.read_parquet(f"{inf_cfg['cell_data_path']}/outlet_cluster_definitions.parquet")

    item_eval = evaluate_by_item(buffered, item_meta, eval_start, eval_end)
    cluster_eval = evaluate_by_outlet_cluster(buffered, outlet_clusters, eval_start, eval_end)

    item_eval.to_csv(f"{output_path}/eval_by_item.csv", index=False)
    cluster_eval.to_csv(f"{output_path}/eval_by_outlet_cluster.csv", index=False)

    print(f"Eval window: {eval_start} → {eval_end}")
    print(f"\nWrote {len(item_eval)} items → {output_path}/eval_by_item.csv")
    print(f"Wrote {len(cluster_eval)} clusters → {output_path}/eval_by_outlet_cluster.csv")

    print("\n--- Per-Item Evaluation ---")
    pd.set_option("display.float_format", "{:.4f}".format)
    pd.set_option("display.max_columns", 20)
    pd.set_option("display.width", 160)
    print(item_eval[["item_code", "demand_class", "total_actual",
                      "wape_raw", "mape_raw", "wape_buffered", "mape_buffered"]].to_string(index=False))

    print("\n--- Per-Outlet-Cluster Evaluation ---")
    print(cluster_eval[["cluster_definition", "n_outlets", "total_actual",
                         "wape_raw", "mape_raw", "wape_buffered", "mape_buffered"]].to_string(index=False))


if __name__ == "__main__":
    main()
