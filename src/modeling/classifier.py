import mlflow
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from xgboost import XGBClassifier

from src.modeling.search import randomized_grid_search
from src.modeling.model_io import save_model


def train_classifier(df_train, df_eval, feature_cols, target_col,
                     param_grid, cfg, model_name):
    """Train and evaluate Stage-1 XGBoost binary classifier for lumpy demand.

    Returns:
        Fitted XGBClassifier (best model from search).
    """
    mod_cfg = cfg["modeling"]

    X_train = df_train[feature_cols].values.astype("float32")
    y_train = df_train[target_col].values.astype("float32")
    X_eval = df_eval[feature_cols].values.astype("float32")
    y_eval = df_eval[target_col].values.astype("float32")

    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0

    base_estimator = XGBClassifier(
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

    with mlflow.start_run(run_name=model_name):
        mlflow.log_params({
            "model_name": model_name,
            "scale_pos_weight": scale_pos_weight,
            "train_start": mod_cfg["train_start"],
            "train_end": mod_cfg["train_end"],
            "eval_start": mod_cfg["eval_start"],
            "eval_end": mod_cfg["eval_end"],
        })

        clf = randomized_grid_search(
            estimator=base_estimator,
            param_grid=param_grid,
            X_train=X_train,
            y_train=y_train,
            n_iter=mod_cfg["n_iter"],
            cv_splits=mod_cfg["cv_splits"],
            scoring="f1",
            random_state=mod_cfg["random_state"],
            mlflow_run_name=f"{model_name}_search",
        )

        threshold = mod_cfg["classifier_threshold"]
        y_proba = clf.predict_proba(X_eval)[:, 1]
        y_pred = (y_proba >= threshold).astype(int)

        mlflow.log_metrics({
            "eval_f1": f1_score(y_eval, y_pred, zero_division=0),
            "eval_precision": precision_score(y_eval, y_pred, zero_division=0),
            "eval_recall": recall_score(y_eval, y_pred, zero_division=0),
            "eval_auc": roc_auc_score(y_eval, y_proba),
        })

        output_dir = cfg["modeling"]["model_output_path"]
        save_model(clf, output_dir, model_name)
        mlflow.log_artifact(f"{output_dir}/{model_name}.pkl")

    return clf
