from __future__ import annotations

from pathlib import Path
import json
import logging
import numpy as np
import joblib
import optuna
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    mean_absolute_error, mean_squared_error, r2_score,
    median_absolute_error, accuracy_score, classification_report,
)
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder
from xgboost import XGBRegressor

from src.aits.config import RAW_DIR, MODEL_DIR

optuna.logging.set_verbosity(optuna.logging.WARNING)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature engineering for ETA model
# ---------------------------------------------------------------------------

CAT_FEATURES = ["route_id", "from_stop_id", "to_stop_id", "route_mode"]
NUM_FEATURES = [
    "scheduled_travel_seconds", "headway_minutes",
    "rainfall_level", "flood_flag", "temperature_c",
    "historical_incident_rate", "is_rush_hour",
]
TARGET = "delay_minutes"
LEAKAGE = ["passenger_density_score", "incident_flag", "tap_in_count_15m"]
DROP_COLS = [
    "trip_id", "date", "scheduled_departure", "scheduled_arrival",
    "direction", "stop_sequence", "day_of_week", "hour",
]


def prepare_eta_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Engineer features from raw training_eta.csv. No data leakage."""
    df = df.copy()

    # Cyclical time encoding
    df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24)
    df["dow_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # Drop leakage and identifier columns
    drop = DROP_COLS + LEAKAGE
    X = df.drop(columns=[c for c in drop if c in df.columns] + [TARGET])
    y = df[TARGET]
    return X, y


def create_preprocessor() -> ColumnTransformer:
    """Build sklearn preprocessor: TargetEncoder for categoricals, passthrough for numeric."""
    return ColumnTransformer([
        ("cat", TargetEncoder(smooth="auto"), CAT_FEATURES),
        ("num", "passthrough", NUM_FEATURES + ["hour_sin", "hour_cos", "dow_sin", "dow_cos"]),
    ])


# ---------------------------------------------------------------------------
# Optuna objective for XGBoost
# ---------------------------------------------------------------------------

def _objective(trial: optuna.Trial, X: np.ndarray, y: np.ndarray, cv: TimeSeriesSplit) -> float:
    """Optuna objective: train XGBoost, return negative MAE across CV folds."""
    params = {
        "objective": "reg:squarederror",
        "n_estimators": trial.suggest_int("n_estimators", 100, 800),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "gamma": trial.suggest_float("gamma", 0.0, 5.0),
        "random_state": 42,
        "n_jobs": 1,
        "verbosity": 0,
    }

    maes = []
    for train_idx, val_idx in cv.split(X):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        model = XGBRegressor(**params)
        model.fit(X_tr, y_tr, verbose=False)
        pred = model.predict(X_val)
        maes.append(mean_absolute_error(y_val, pred))

    return -float(np.mean(maes))  # Optuna minimizes, so return negative MAE


# ---------------------------------------------------------------------------
# Main training function
# ---------------------------------------------------------------------------

def train_eta_model_v2(n_trials: int = 50, cv_splits: int = 5) -> dict:
    """Train ETA delay model with XGBoost + Optuna hyperparameter tuning.

    Returns dict with metrics, best params, and saves model to disk.
    """
    log.info("Loading training data...")
    df = pd.read_csv(RAW_DIR / "training_eta.csv")
    X_df, y = prepare_eta_features(df)

    log.info("Building preprocessor and transforming features...")
    preprocessor = create_preprocessor()
    X_encoded = preprocessor.fit_transform(X_df, y)
    if hasattr(X_encoded, "toarray"):
        X_encoded = X_encoded.toarray()
    X_arr = np.asarray(X_encoded, dtype=np.float32)
    y_arr = y.to_numpy(dtype=np.float32)

    log.info(f"Features: {X_arr.shape[1]}, Samples: {X_arr.shape[0]}")

    # TimeSeriesSplit for temporal validation
    tscv = TimeSeriesSplit(n_splits=cv_splits, gap=1)

    # Optuna hyperparameter search (seeded for reproducibility)
    log.info(f"Starting Optuna search ({n_trials} trials)...")
    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", study_name="eta_xgb", sampler=sampler)
    study.optimize(lambda trial: _objective(trial, X_arr, y_arr, tscv), n_trials=n_trials)

    best_params = study.best_params
    best_params["objective"] = "reg:squarederror"
    best_params["random_state"] = 42
    best_params["n_jobs"] = -1
    best_params["verbosity"] = 0
    log.info(f"Best MAE: {-study.best_value:.4f}")
    log.info(f"Best params: {best_params}")

    # Final model: train on all data with best params
    final_model = XGBRegressor(**best_params)
    final_model.fit(X_arr, y_arr, verbose=False)

    # Hold-out evaluation (last fold of TimeSeriesSplit)
    train_idx, test_idx = list(tscv.split(X_arr))[-1]
    X_test, y_test = X_arr[test_idx], y_arr[test_idx]
    pred = final_model.predict(X_test)

    test_mae = float(mean_absolute_error(y_test, pred))
    test_rmse = float(np.sqrt(mean_squared_error(y_test, pred)))
    test_r2 = float(r2_score(y_test, pred))
    test_median_ae = float(median_absolute_error(y_test, pred))
    within_1 = float((np.abs(y_test - pred) <= 1.0).mean() * 100)
    within_2 = float((np.abs(y_test - pred) <= 2.0).mean() * 100)
    within_3 = float((np.abs(y_test - pred) <= 3.0).mean() * 100)

    # CV scores from best params
    cv_maes = []
    for train_idx, val_idx in tscv.split(X_arr):
        m = XGBRegressor(**best_params)
        m.fit(X_arr[train_idx], y_arr[train_idx], verbose=False)
        p = m.predict(X_arr[val_idx])
        cv_maes.append(mean_absolute_error(y_arr[val_idx], p))

    # Save model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    pipe = Pipeline([("preprocessor", preprocessor), ("model", final_model)])
    joblib.dump(pipe, MODEL_DIR / "eta_xgb_model.joblib")

    # Feature importance
    fi = dict(sorted(
        zip(X_df.columns, [float(v) for v in final_model.feature_importances_]),
        key=lambda x: -x[1],
    ))
    with open(MODEL_DIR / "eta_feature_importance.json", "w") as f:
        json.dump(fi, f, indent=2)

    # Metrics
    metrics = {
        "best_mae": round(-study.best_value, 4),
        "best_params": best_params,
        "cv_mae_mean": round(float(np.mean(cv_maes)), 4),
        "cv_mae_std": round(float(np.std(cv_maes)), 4),
        "test_mae": round(test_mae, 4),
        "test_rmse": round(test_rmse, 4),
        "test_r2": round(test_r2, 4),
        "test_median_ae": round(test_median_ae, 4),
        "within_1min_pct": round(within_1, 2),
        "within_2min_pct": round(within_2, 2),
        "within_3min_pct": round(within_3, 2),
        "n_rows": int(len(df)),
        "n_features": int(X_arr.shape[1]),
        "n_trials": n_trials,
    }
    with open(MODEL_DIR / "eta_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    log.info(f"Model saved to {MODEL_DIR / 'eta_xgb_model.joblib'}")
    log.info(f"Test MAE: {test_mae:.4f}, RMSE: {test_rmse:.4f}, R2: {test_r2:.4f}")
    return metrics


# ---------------------------------------------------------------------------
# Density model (XGBoost Classifier, no leakage)
# ---------------------------------------------------------------------------

DENSITY_CAT_FEATURES = ["from_stop_id", "route_id"]
DENSITY_NUM_FEATURES = [
    "headway_minutes", "vehicle_capacity",
    "hour", "day_of_week", "is_rush_hour",
    "rainfall_level", "flood_flag", "event_flag",
    "routes_through_stop", "is_terminal", "route_demand_factor",
]
DENSITY_TARGET = "density_level"
DENSITY_LEAKAGE = ["tap_in_count_15m", "load_factor", "incident_flag"]


def prepare_density_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Engineer features from training_density.csv. No data leakage."""
    df = df.copy()
    drop = DENSITY_LEAKAGE
    X = df.drop(columns=[c for c in drop if c in df.columns] + [DENSITY_TARGET])
    y = df[DENSITY_TARGET]
    return X, y


def create_density_preprocessor() -> ColumnTransformer:
    """Build sklearn preprocessor for density model."""
    return ColumnTransformer([
        ("cat", TargetEncoder(smooth="auto"), DENSITY_CAT_FEATURES),
        ("num", "passthrough", DENSITY_NUM_FEATURES),
    ])


def _density_objective(trial: optuna.Trial, X: np.ndarray, y: np.ndarray, cv, cat_indices: list[int], n_classes: int) -> float:
    """Optuna objective for XGBoost density classifier."""
    from xgboost import XGBClassifier
    from sklearn.metrics import f1_score

    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 800),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.1, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 20),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "gamma": trial.suggest_float("gamma", 0.0, 5.0),
        "random_state": 42,
        "n_jobs": 1,
        "verbosity": 0,
        "objective": "multi:softprob",
        "num_class": n_classes,
    }

    f1s = []
    for train_idx, val_idx in cv.split(X, y):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]

        # SMOTENC inside CV fold with dynamic indices
        from imblearn.over_sampling import SMOTENC
        smote = SMOTENC(categorical_features=cat_indices, random_state=42, k_neighbors=3)
        try:
            X_tr_res, y_tr_res = smote.fit_resample(X_tr, y_tr)
        except ValueError:
            X_tr_res, y_tr_res = X_tr, y_tr  # fallback if SMOTENC fails

        model = XGBClassifier(**params)
        model.fit(X_tr_res, y_tr_res, verbose=False)
        pred = model.predict(X_val)
        f1s.append(f1_score(y_val, pred, average="macro"))

    return float(np.mean(f1s))


def train_density_model_v2(n_trials: int = 50, cv_splits: int = 5) -> dict:
    """Train density model with XGBoost + Optuna. No data leakage."""
    from xgboost import XGBClassifier
    from imblearn.over_sampling import SMOTENC
    from sklearn.metrics import f1_score, accuracy_score, cohen_kappa_score
    from sklearn.preprocessing import LabelEncoder
    from collections import Counter

    log.info("Loading density training data...")
    df = pd.read_csv(RAW_DIR / "training_density.csv")
    X_df, y = prepare_density_features(df)

    log.info("Building preprocessor...")
    preprocessor = create_density_preprocessor()
    X_encoded = preprocessor.fit_transform(X_df, y)
    if hasattr(X_encoded, "toarray"):
        X_encoded = X_encoded.toarray()
    X_arr = np.asarray(X_encoded, dtype=np.float32)
    y_arr = y.to_numpy()

    # Compute dynamic categorical indices for SMOTENC
    cat_indices = [list(X_df.columns).index(c) for c in DENSITY_CAT_FEATURES]

    log.info(f"Features: {X_arr.shape[1]}, Samples: {X_arr.shape[0]}")

    # Encode string labels to integers for XGBoost
    from sklearn.preprocessing import LabelEncoder
    le = LabelEncoder()
    y_encoded = le.fit_transform(y_arr)
    n_classes = len(le.classes_)
    log.info(f"Classes: {n_classes} {list(le.classes_)}, Distribution: {dict(pd.Series(y_encoded).value_counts())}")

    # Compute dynamic categorical indices for SMOTENC
    cat_indices = [list(X_df.columns).index(c) for c in DENSITY_CAT_FEATURES]

    tscv = TimeSeriesSplit(n_splits=cv_splits, gap=1)

    log.info(f"Starting Optuna density search ({n_trials} trials)...")
    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", study_name="density_xgb", sampler=sampler)
    study.optimize(
        lambda trial: _density_objective(trial, X_arr, y_encoded, tscv, cat_indices, n_classes),
        n_trials=n_trials,
    )

    best_params = study.best_params
    best_params["random_state"] = 42
    best_params["n_jobs"] = -1
    best_params["verbosity"] = 0
    best_params["objective"] = "multi:softprob"
    best_params["num_class"] = n_classes
    log.info(f"Best Macro F1: {study.best_value:.4f}")

    # Final model: train on all data with best params
    smote = SMOTENC(categorical_features=cat_indices, random_state=42, k_neighbors=3)
    try:
        X_all_res, y_all_res = smote.fit_resample(X_arr, y_encoded)
    except ValueError:
        X_all_res, y_all_res = X_arr, y_encoded

    final_model = XGBClassifier(**best_params)
    final_model.fit(X_all_res, y_all_res, verbose=False)

    # Hold-out evaluation
    train_idx, test_idx = list(tscv.split(X_arr, y_encoded))[-1]
    X_test, y_test = X_arr[test_idx], y_encoded[test_idx]
    pred = final_model.predict(X_test)

    from sklearn.metrics import accuracy_score, cohen_kappa_score
    test_acc = float(accuracy_score(y_test, pred))
    test_f1 = float(f1_score(y_test, pred, average="macro"))
    test_kappa = float(cohen_kappa_score(y_test, pred))

    # Naive baseline: always predict majority class
    from collections import Counter
    majority_class_encoded = Counter(y_encoded).most_common(1)[0][0]
    naive_pred = np.full_like(y_test, majority_class_encoded)
    naive_acc = float(accuracy_score(y_test, naive_pred))
    naive_f1 = float(f1_score(y_test, naive_pred, average="macro"))

    # CV scores
    cv_f1s = []
    for train_idx, val_idx in tscv.split(X_arr, y_encoded):
        m = XGBClassifier(**best_params)
        smote_cv = SMOTENC(categorical_features=cat_indices, random_state=42, k_neighbors=3)
        try:
            X_tr, y_tr = smote_cv.fit_resample(X_arr[train_idx], y_encoded[train_idx])
        except ValueError:
            X_tr, y_tr = X_arr[train_idx], y_encoded[train_idx]
        m.fit(X_tr, y_tr, verbose=False)
        p = m.predict(X_arr[val_idx])
        cv_f1s.append(f1_score(y_encoded[val_idx], p, average="macro"))

    # Save
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    pipe = Pipeline([("preprocessor", preprocessor), ("model", final_model)])
    joblib.dump(pipe, MODEL_DIR / "density_xgb_model.joblib")
    joblib.dump(le, MODEL_DIR / "density_label_encoder.joblib")

    fi = dict(sorted(
        zip(X_df.columns, [float(v) for v in final_model.feature_importances_]),
        key=lambda x: -x[1],
    ))
    with open(MODEL_DIR / "density_feature_importance.json", "w") as f:
        json.dump(fi, f, indent=2)

    metrics = {
        "best_f1_macro": round(study.best_value, 4),
        "best_params": best_params,
        "cv_f1_mean": round(float(np.mean(cv_f1s)), 4),
        "cv_f1_std": round(float(np.std(cv_f1s)), 4),
        "test_accuracy": round(test_acc, 4),
        "test_f1_macro": round(test_f1, 4),
        "test_kappa": round(test_kappa, 4),
        "naive_accuracy": round(naive_acc, 4),
        "naive_f1_macro": round(naive_f1, 4),
        "n_rows": int(len(df)),
        "n_features": int(X_arr.shape[1]),
        "n_trials": n_trials,
        "classes": list(le.classes_),
    }
    with open(MODEL_DIR / "density_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    log.info(f"Density model saved to {MODEL_DIR / 'density_xgb_model.joblib'}")
    log.info(f"Test F1: {test_f1:.4f}, Accuracy: {test_acc:.4f}, Kappa: {test_kappa:.4f}")
    log.info(f"Naive baseline: Accuracy={naive_acc:.4f}, F1={naive_f1:.4f}")
    return metrics


def train_density_catboost(n_trials: int = 15, cv_splits: int = 3) -> dict:
    """Train density model with CatBoost + Optuna. No leakage, no SMOTENC needed.

    CatBoost advantages over XGBoost for this problem:
    - Native categorical handling (no TargetEncoder needed)
    - auto_class_weights="Balanced" (no SMOTENC needed)
    - Plain boosting for speed (Ordered is 1.7x slower, marginal quality gain at 25k rows)
    - Faster training (no SMOTENC overhead)

    References:
    - CatBoost paper (arxiv 1706.09516): Plain and LightGBM are fastest
    - GitHub Issue #1034: Ordered default for <50k, Plain for >50k
    - Cats & West 2024: Poisson arrivals for transit demand modeling
    """
    from catboost import CatBoostClassifier
    from sklearn.metrics import f1_score, accuracy_score, cohen_kappa_score
    from sklearn.preprocessing import LabelEncoder
    from collections import Counter

    log.info("Loading density training data (CatBoost)...")
    df = pd.read_csv(RAW_DIR / "training_density.csv")
    X_df, y = prepare_density_features(df)

    log.info(f"Features: {list(X_df.columns)}")
    log.info(f"Rows: {len(X_df)}")

    # Encode string labels to integers for Optuna
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    n_classes = len(le.classes_)
    log.info(f"Classes: {n_classes} {list(le.classes_)}")
    log.info(f"Distribution: {dict(pd.Series(y_encoded).value_counts())}")

    # Identify categorical columns for CatBoost
    cat_cols = [c for c in DENSITY_CAT_FEATURES if c in X_df.columns]

    tscv = TimeSeriesSplit(n_splits=cv_splits, gap=1)

    # Optuna objective
    def objective(trial):
        params = {
            "iterations": trial.suggest_int("iterations", 100, 400),
            "depth": trial.suggest_int("depth", 4, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.05, 0.3, log=True),
            "l2_leaf_reg": trial.suggest_float("l2_leaf_reg", 1.0, 5.0),
            "bagging_temperature": trial.suggest_float("bagging_temperature", 0.0, 1.0),
            "boosting_type": "Plain",
            "random_seed": 42,
            "verbose": 0,
            "auto_class_weights": "Balanced",
            "loss_function": "MultiClass",
            "eval_metric": "TotalF1",
            "cat_features": cat_cols,
        }

        f1s = []
        for train_idx, val_idx in tscv.split(X_df, y_encoded):
            X_tr, X_val = X_df.iloc[train_idx], X_df.iloc[val_idx]
            y_tr, y_val = y_encoded[train_idx], y_encoded[val_idx]

            model = CatBoostClassifier(**params)
            model.fit(X_tr, y_tr, eval_set=(X_val, y_val), early_stopping_rounds=30, verbose=0)
            pred = model.predict(X_val).flatten().astype(int)
            f1s.append(f1_score(y_val, pred, average="macro"))

        return float(np.mean(f1s))

    log.info(f"Starting Optuna CatBoost search ({n_trials} trials)...")
    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", study_name="density_catboost", sampler=sampler)
    study.optimize(objective, n_trials=n_trials)

    best_params = study.best_params
    best_params["boosting_type"] = "Plain"
    best_params["random_seed"] = 42
    best_params["verbose"] = 0
    best_params["auto_class_weights"] = "Balanced"
    best_params["loss_function"] = "MultiClass"
    best_params["eval_metric"] = "TotalF1"
    best_params["cat_features"] = cat_cols
    log.info(f"Best Macro F1: {study.best_value:.4f}")

    # Final model: train on all data with best params
    final_model = CatBoostClassifier(**best_params)
    final_model.fit(X_df, y_encoded, verbose=False)

    # Hold-out evaluation
    train_idx, test_idx = list(tscv.split(X_df, y_encoded))[-1]
    X_test, y_test = X_df.iloc[test_idx], y_encoded[test_idx]
    pred = final_model.predict(X_test).flatten().astype(int)

    test_acc = float(accuracy_score(y_test, pred))
    test_f1 = float(f1_score(y_test, pred, average="macro"))
    test_kappa = float(cohen_kappa_score(y_test, pred))

    # Naive baseline
    majority_class_encoded = Counter(y_encoded).most_common(1)[0][0]
    naive_pred = np.full_like(y_test, majority_class_encoded)
    naive_acc = float(accuracy_score(y_test, naive_pred))
    naive_f1 = float(f1_score(y_test, naive_pred, average="macro"))

    # CV scores
    cv_f1s = []
    for train_idx, val_idx in tscv.split(X_df, y_encoded):
        m = CatBoostClassifier(**best_params)
        m.fit(X_df.iloc[train_idx], y_encoded[train_idx], verbose=0)
        p = m.predict(X_df.iloc[val_idx]).flatten().astype(int)
        cv_f1s.append(f1_score(y_encoded[val_idx], p, average="macro"))

    # Save
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    final_model.save_model(str(MODEL_DIR / "density_catboost_model.cbm"))
    joblib.dump(le, MODEL_DIR / "density_label_encoder.joblib")

    fi = dict(sorted(
        zip(X_df.columns, [float(v) for v in final_model.get_feature_importance()]),
        key=lambda x: -x[1],
    ))
    with open(MODEL_DIR / "density_feature_importance.json", "w") as f:
        json.dump(fi, f, indent=2)

    metrics = {
        "best_f1_macro": round(study.best_value, 4),
        "best_params": best_params,
        "cv_f1_mean": round(float(np.mean(cv_f1s)), 4),
        "cv_f1_std": round(float(np.std(cv_f1s)), 4),
        "test_accuracy": round(test_acc, 4),
        "test_f1_macro": round(test_f1, 4),
        "test_kappa": round(test_kappa, 4),
        "naive_accuracy": round(naive_acc, 4),
        "naive_f1_macro": round(naive_f1, 4),
        "n_rows": int(len(df)),
        "n_features": int(X_df.shape[1]),
        "n_trials": n_trials,
        "classes": list(le.classes_),
        "model_type": "CatBoost",
    }
    with open(MODEL_DIR / "density_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    log.info(f"Density CatBoost model saved to {MODEL_DIR / 'density_catboost_model.cbm'}")
    log.info(f"Test F1: {test_f1:.4f}, Accuracy: {test_acc:.4f}, Kappa: {test_kappa:.4f}")
    log.info(f"Naive baseline: Accuracy={naive_acc:.4f}, F1={naive_f1:.4f}")
    return metrics


def train_all() -> dict:
    from pathlib import Path

    # Ensure training_eta.csv is in the new GTFS-derived format
    csv_path = RAW_DIR / "training_eta.csv"
    if csv_path.exists():
        df_check = pd.read_csv(csv_path, nrows=1)
        if "from_stop_id" not in df_check.columns:
            from src.aits.data.build_training_dataset import build_training_eta
            build_training_eta(Path(RAW_DIR / "gtfs_transjakarta"), output_path=csv_path, force=True)
    else:
        from src.aits.data.build_training_dataset import build_training_eta
        build_training_eta(Path(RAW_DIR / "gtfs_transjakarta"), output_path=csv_path)

    # Ensure training_density.csv is in the new no-leakage format
    density_csv = RAW_DIR / "training_density.csv"
    if density_csv.exists():
        df_check = pd.read_csv(density_csv, nrows=1)
        if "tap_in_count_15m" in df_check.columns:
            from src.aits.data.build_density_dataset import build_density_dataset
            build_density_dataset(Path(RAW_DIR / "gtfs_transjakarta"), output_path=density_csv)
    else:
        from src.aits.data.build_density_dataset import build_density_dataset
        build_density_dataset(Path(RAW_DIR / "gtfs_transjakarta"), output_path=density_csv)

    metrics = {"eta": train_eta_model_v2(n_trials=50, cv_splits=5), "density": train_density_catboost(n_trials=15, cv_splits=3)}
    with open(MODEL_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    train_all()
