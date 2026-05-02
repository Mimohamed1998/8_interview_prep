"""Inference pipeline — scores all 9 grid-cell models over the inference window."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.common.utils.config import load_config
from src.common.data_utils import write_parquet
from src.model_prediction_pipelines.model_prediction import run_inference


def build_predictions(cfg):
    """Load data, run inference across all grid cells, and return combined DataFrame.

    Args:
        cfg: Full project config dict.

    Returns:
        DataFrame with outlet_id, item_code, year_month, predicted_qty, cell_name.
    """
    return run_inference(cfg)


def main():
    """Entry point: run inference and write predictions to the intermediate layer."""
    cfg = load_config()
    output_path = cfg["inference"]["output_path"]

    predictions = build_predictions(cfg)

    write_parquet(predictions, f"{output_path}/predictions.parquet")
    print(f"Wrote {len(predictions):,} rows → {output_path}/predictions.parquet")


if __name__ == "__main__":
    main()
