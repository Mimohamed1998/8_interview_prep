import pickle
from pathlib import Path


def save_model(model, output_dir, model_name):
    """Serialise a fitted model to .pkl.

    Returns:
        Path to saved .pkl file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{model_name}.pkl"
    with open(path, "wb") as f:
        pickle.dump(model, f)
    return path


def load_model(output_dir, model_name):
    """Load a .pkl model from disk.

    Returns:
        Fitted estimator.
    """
    path = Path(output_dir) / f"{model_name}.pkl"
    with open(path, "rb") as f:
        return pickle.load(f)
