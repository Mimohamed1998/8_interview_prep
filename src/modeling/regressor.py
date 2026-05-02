import numpy as np
import mlflow
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor

from src.modeling.search import randomized_grid_search
from src.modeling.metrics import mape, wmape
from src.modeling.model_io import save_model


def train_regressor(df_train, df_eval, feature_cols, target_col,
                    param_grid, cfg, model_name):
    """Train and evaluate a single-stage XGBoost regressor with grid search.

    Returns:
        Fitted XGBRegressor (best model from search).
    """
    mod_cfg = cfg["modeling"]

    # Clean data: remove rows with NaN or inf in target
    n_train_before = len(df_train)
    n_eval_before = len(df_eval)
    df_train = df_train[df_train[target_col].notna() & np.isfinite(df_train[target_col])]
    df_eval = df_eval[df_eval[target_col].notna() & np.isfinite(df_eval[target_col])]
    print(f"[{model_name}] train: {n_train_before} rows → {len(df_train)} kept ({n_train_before - len(df_train)} removed)")
    print(f"[{model_name}] eval:  {n_eval_before} rows → {len(df_eval)} kept ({n_eval_before - len(df_eval)} removed)")

    X_train = df_train[feature_cols].values.astype(np.float32)
    y_train = df_train[target_col].values.astype(np.float32)
    X_eval = df_eval[feature_cols].values.astype(np.float32)
    y_eval_log = df_eval[target_col].values.astype(np.float32)
    y_eval_raw = df_eval["target_qty_raw"].values.astype(np.float32)
    y_train_raw = df_train["target_qty_raw"].values.astype(np.float32)

    base_estimator = XGBRegressor(
        objective="reg:squarederror",
        tree_method="hist",
        device="cpu",
        random_state=mod_cfg["random_state"],
        nthread=1,
    )

    mlflow.set_tracking_uri(mod_cfg["mlflow_tracking_uri"])
    mlflow.set_experiment(mod_cfg["mlflow_experiment"])

    with mlflow.start_run(run_name=model_name):
        mlflow.log_params({
            "model_name": model_name,
            "train_start": mod_cfg["train_start"],
            "train_end": mod_cfg["train_end"],
            "eval_start": mod_cfg["eval_start"],
            "eval_end": mod_cfg["eval_end"],
            "n_iter": mod_cfg["n_iter"],
            "cv_splits": mod_cfg["cv_splits"],
        })

        reg = randomized_grid_search(
            estimator=base_estimator,
            param_grid=param_grid,
            X_train=X_train,
            y_train=y_train,
            n_iter=mod_cfg["n_iter"],
            cv_splits=mod_cfg["cv_splits"],
            scoring="neg_mean_absolute_error",
            random_state=mod_cfg["random_state"],
            mlflow_run_name=f"{model_name}_search",
        )

        # Eval metrics (back-transformed to raw units)
        y_pred_log = reg.predict(X_eval)
        y_pred_raw = np.expm1(y_pred_log)

        eval_mape, eval_zero_frac = mape(y_eval_raw, y_pred_raw)
        eval_wmape = wmape(y_eval_raw, y_pred_raw)
        eval_mae = mean_absolute_error(y_eval_log, y_pred_log)
        eval_rmse = float(np.sqrt(mean_squared_error(y_eval_log, y_pred_log)))

        # Train metrics (overfitting check)
        y_train_pred_log = reg.predict(X_train)
        y_train_pred_raw = np.expm1(y_train_pred_log)
        train_mape, _ = mape(y_train_raw, y_train_pred_raw)
        train_wmape = wmape(y_train_raw, y_train_pred_raw)

        mlflow.log_metrics({
            "eval_wmape": eval_wmape,
            "eval_mape": eval_mape,
            "eval_zero_fraction": eval_zero_frac,
            "eval_mae": eval_mae,
            "eval_rmse": eval_rmse,
            "train_wmape": train_wmape,
            "train_mape": train_mape,
        })

        output_dir = cfg["modeling"]["model_output_path"]
        save_model(reg, output_dir, model_name)
        mlflow.log_artifact(f"{output_dir}/{model_name}.pkl")

    return reg
