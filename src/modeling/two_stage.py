import numpy as np
import mlflow
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import f1_score, roc_auc_score

from src.modeling.search import randomized_grid_search
from src.modeling.metrics import mape, wmape
from src.modeling.model_io import save_model


def train_two_stage(df_train, df_eval, feature_cols, cfg, model_name_prefix):
    """Train the two-stage classifier+regressor for lumpy demand cells.

    Stage 1: XGBClassifier on target_is_nonzero (all rows).
    Stage 2: XGBRegressor on target_qty_log1p (nonzero-demand rows only).

    Returns:
        Tuple of (stage1_classifier, stage2_regressor).
    """
    mod_cfg = cfg["modeling"]
    param_grid = mod_cfg["xgb_param_grid"]

    X_train = df_train[feature_cols].values.astype("float32")
    X_eval = df_eval[feature_cols].values.astype("float32")
    y_train_binary = df_train["target_is_nonzero"].values.astype("float32")
    y_eval_binary = df_eval["target_is_nonzero"].values.astype("float32")
    y_eval_raw = df_eval["target_qty_raw"].values.astype("float32")

    # Stage 1 — classifier
    n_neg = (y_train_binary == 0).sum()
    n_pos = (y_train_binary == 1).sum()
    scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

    clf_base = XGBClassifier(
        objective="binary:logistic",
        tree_method="hist",
        device="cpu",
        scale_pos_weight=scale_pos_weight,
        random_state=mod_cfg["random_state"],
        nthread=1,
        eval_metric="logloss",
    )

    mlflow.set_tracking_uri(mod_cfg["mlflow_tracking_uri"])
    mlflow.set_experiment(mod_cfg["mlflow_experiment"])

    with mlflow.start_run(run_name=model_name_prefix):
        mlflow.log_params({
            "model_name_prefix": model_name_prefix,
            "scale_pos_weight": scale_pos_weight,
            "train_start": mod_cfg["train_start"],
            "train_end": mod_cfg["train_end"],
            "eval_start": mod_cfg["eval_start"],
            "eval_end": mod_cfg["eval_end"],
        })

        clf = randomized_grid_search(
            estimator=clf_base,
            param_grid=param_grid,
            X_train=X_train,
            y_train=y_train_binary,
            n_iter=mod_cfg["n_iter"],
            cv_splits=mod_cfg["cv_splits"],
            scoring="f1",
            random_state=mod_cfg["random_state"],
            mlflow_run_name=f"{model_name_prefix}_stage1_search",
        )

        threshold = mod_cfg["classifier_threshold"]
        y_proba = clf.predict_proba(X_eval)[:, 1]
        y_clf_pred = (y_proba >= threshold).astype(int)
        mlflow.log_metrics({
            "stage1_eval_f1": f1_score(y_eval_binary, y_clf_pred, zero_division=0),
            "stage1_eval_auc": roc_auc_score(y_eval_binary, y_proba),
        })

        # Stage 2 — regressor on nonzero-demand training rows only
        nonzero_mask_train = df_train["target_is_nonzero"] == 1
        df_train_nz = df_train[nonzero_mask_train]
        X_train_nz = df_train_nz[feature_cols].values.astype("float32")
        y_train_nz = df_train_nz["target_qty_log1p"].values.astype("float32")

        reg_base = XGBRegressor(
            objective="reg:squarederror",
            tree_method="hist",
            device="cpu",
            random_state=mod_cfg["random_state"],
            nthread=1,
        )

        reg = randomized_grid_search(
            estimator=reg_base,
            param_grid=param_grid,
            X_train=X_train_nz,
            y_train=y_train_nz,
            n_iter=mod_cfg["n_iter"],
            cv_splits=mod_cfg["cv_splits"],
            scoring="neg_mean_absolute_error",
            random_state=mod_cfg["random_state"],
            mlflow_run_name=f"{model_name_prefix}_stage2_search",
        )

        # Combined eval
        y_pred_raw = predict_two_stage(clf, reg, X_eval, threshold)
        eval_mape, eval_zero_frac = mape(y_eval_raw, y_pred_raw)
        eval_wmape = wmape(y_eval_raw, y_pred_raw)
        mlflow.log_metrics({
            "eval_wmape": eval_wmape,
            "eval_mape": eval_mape,
            "eval_zero_fraction": eval_zero_frac,
        })

        output_dir = cfg["modeling"]["model_output_path"]
        save_model(clf, output_dir, f"{model_name_prefix}_stage1_clf")
        save_model(reg, output_dir, f"{model_name_prefix}_stage2_reg")

    return clf, reg


def predict_two_stage(clf, reg, X, threshold):
    """Generate combined two-stage prediction.

    Returns:
        Array of predicted raw quantities (0 where Stage 1 predicts zero event).
    """
    X = np.asarray(X)
    y_proba = clf.predict_proba(X)[:, 1]
    nonzero_mask = y_proba >= threshold
    y_pred = np.zeros(len(X), dtype=float)
    if nonzero_mask.any():
        y_pred_log = reg.predict(X[nonzero_mask])
        y_pred[nonzero_mask] = np.expm1(y_pred_log)
    return y_pred
