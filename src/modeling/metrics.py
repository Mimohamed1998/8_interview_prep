import numpy as np


def mape(y_true, y_pred, eps=1e-8):
    """Mean Absolute Percentage Error on raw-unit scale, excluding zero actuals.

    Returns:
        Tuple of (mape_value: float, zero_fraction: float).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    nonzero_mask = y_true != 0
    zero_fraction = 1.0 - nonzero_mask.mean()
    if nonzero_mask.sum() == 0:
        return 0.0, zero_fraction
    mape_val = np.mean(np.abs(y_true[nonzero_mask] - y_pred[nonzero_mask]) /
                       (np.abs(y_true[nonzero_mask]) + eps)) * 100
    return float(mape_val), float(zero_fraction)


def wmape(y_true, y_pred, eps=1e-8):
    """Weighted Mean Absolute Percentage Error (revenue-weighted).

    Returns:
        wmape_value as float.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sum(np.abs(y_true - y_pred)) / (np.sum(y_true) + eps) * 100)
