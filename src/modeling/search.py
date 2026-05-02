import numpy as np
import mlflow
from sklearn.base import clone
from sklearn.model_selection import ParameterSampler, TimeSeriesSplit, cross_val_score


def randomized_grid_search(estimator, param_grid, X_train, y_train,
                            n_iter, cv_splits, scoring, random_state,
                            mlflow_run_name):
    """Run randomized search with TimeSeriesSplit, printing results after each candidate.

    Returns:
        Best fitted estimator (refit on full X_train).
    """
    tscv = TimeSeriesSplit(n_splits=cv_splits)
    param_list = list(ParameterSampler(param_grid, n_iter=n_iter, random_state=random_state))

    best_score = -np.inf
    best_params = None

    print(f"\n{'='*60}")
    print(f"  {mlflow_run_name}  ({n_iter} candidates, {cv_splits}-fold TimeSeriesCV)")
    print(f"  scoring: {scoring}")
    print(f"{'='*60}")

    with mlflow.start_run(run_name=mlflow_run_name, nested=True):
        for i, params in enumerate(param_list, start=1):
            model = clone(estimator)
            model.set_params(**params)
            scores = cross_val_score(model, X_train, y_train,
                                     cv=tscv, scoring=scoring, n_jobs=1)
            mean_score = scores.mean()
            std_score = scores.std()

            flag = "  <-- best" if mean_score > best_score else ""
            print(f"  [{i:>{len(str(n_iter))}}/{n_iter}]  "
                  f"score={mean_score:+.4f} ± {std_score:.4f}{flag}")
            for k, v in params.items():
                print(f"          {k}: {v}")

            if mean_score > best_score:
                best_score = mean_score
                best_params = params

        print(f"\n  Best CV score : {best_score:+.4f}")
        print(f"  Best params   : {best_params}")
        print(f"{'='*60}\n")

        best_model = clone(estimator)
        best_model.set_params(**best_params)
        best_model.fit(X_train, y_train)

        mlflow.log_params(best_params)
        mlflow.log_metric("best_cv_score", best_score)

    return best_model
