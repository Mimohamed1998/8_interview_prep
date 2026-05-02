"""Buffer pipeline — applies 2-month rolling error correction to inference forecasts."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd

from src.common.utils.config import load_config
from src.common.data_utils import write_parquet
from src.model_prediction_pipelines.buffer import (
    apply_buffer,
    build_buffer_output,
    compute_buffer,
    compute_metrics,
    load_actuals,
)


def main():
    cfg = load_config()
    inf_cfg = cfg["inference"]
    mod_cfg = cfg["modeling"]

    predictions_path = f"{inf_cfg['output_path']}/predictions.parquet"
    output_path = inf_cfg["output_path"]

    predictions = pd.read_parquet(predictions_path)
    actuals = load_actuals(inf_cfg["cell_data_path"])

    merged = predictions.merge(
        actuals,
        on=["outlet_id", "item_code", "year_month"],
        how="left",
    )

    merged = compute_buffer(merged, n_months=10)
    merged = apply_buffer(merged)

    output = build_buffer_output(merged)

    metrics = compute_metrics(merged, mod_cfg["eval_start"], mod_cfg["eval_end"])

    write_parquet(output, f"{output_path}/predictions_buffered.parquet")
    metrics.to_csv(f"{output_path}/buffer_metrics.csv", index=False)

    print(f"Wrote {len(output):,} rows → {output_path}/predictions_buffered.parquet")
    print(f"Wrote metrics → {output_path}/buffer_metrics.csv")
    print("\nBuffer metrics:")
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    main()
