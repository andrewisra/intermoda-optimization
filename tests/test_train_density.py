"""Tests for density model training with XGBoost + Optuna."""
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.aits.ml.train import (
    train_density_model_v2,
    prepare_density_features,
    create_density_preprocessor,
)

RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
GTFS_DIR = RAW_DIR / "gtfs_transjakarta"


@pytest.fixture(scope="session", autouse=True)
def ensure_density_csv():
    """Ensure training_density.csv exists in no-leakage format."""
    from src.aits.data.build_density_dataset import build_density_dataset
    csv_path = RAW_DIR / "training_density.csv"
    if csv_path.exists():
        df_check = pd.read_csv(csv_path, nrows=1)
        if "tap_in_count_15m" in df_check.columns:
            print("Re-generating density CSV (old leaky format detected)...")
            build_density_dataset(GTFS_DIR, output_path=csv_path)
    else:
        print("Generating density CSV...")
        build_density_dataset(GTFS_DIR, output_path=csv_path)


class TestPrepareDensityFeatures:
    def test_returns_dataframe_and_series(self):
        df = pd.read_csv(RAW_DIR / "training_density.csv")
        X, y = prepare_density_features(df)
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)

    def test_no_leakage(self):
        df = pd.read_csv(RAW_DIR / "training_density.csv")
        X, y = prepare_density_features(df)
        for feat in ["tap_in_count_15m", "load_factor", "incident_flag"]:
            assert feat not in X.columns, f"Leakage: {feat}"

    def test_has_expected_features(self):
        df = pd.read_csv(RAW_DIR / "training_density.csv")
        X, y = prepare_density_features(df)
        expected = [
            "from_stop_id", "route_id", "headway_minutes", "vehicle_capacity",
            "hour", "day_of_week", "is_rush_hour",
            "rainfall_level", "flood_flag", "event_flag",
        ]
        for feat in expected:
            assert feat in X.columns, f"Missing: {feat}"

    def test_target_is_density_level(self):
        df = pd.read_csv(RAW_DIR / "training_density.csv")
        X, y = prepare_density_features(df)
        assert y.name == "density_level"
        assert set(y.unique()).issubset({"LOW", "MEDIUM", "HIGH", "OVERLOADED"})


class TestTrainDensityModelV2:
    def test_returns_dict_with_expected_keys(self):
        result = train_density_model_v2(n_trials=2, cv_splits=3)
        assert "test_f1_macro" in result
        assert "test_accuracy" in result
        assert "test_kappa" in result
        assert "naive_accuracy" in result
        assert "naive_f1_macro" in result
        assert "cv_f1_mean" in result
        assert "best_params" in result

    def test_model_beats_naive_baseline(self):
        result = train_density_model_v2(n_trials=2, cv_splits=3)
        assert result["test_f1_macro"] > result["naive_f1_macro"], \
            f"Model F1 ({result['test_f1_macro']}) should beat naive ({result['naive_f1_macro']})"

    def test_model_saved(self):
        result = train_density_model_v2(n_trials=2, cv_splits=3)
        assert (MODEL_DIR / "density_xgb_model.joblib").exists()

    def test_metrics_saved(self):
        result = train_density_model_v2(n_trials=2, cv_splits=3)
        assert (MODEL_DIR / "density_metrics.json").exists()
        with open(MODEL_DIR / "density_metrics.json") as f:
            loaded = json.load(f)
        assert "test_f1_macro" in loaded

    def test_feature_importance_saved(self):
        result = train_density_model_v2(n_trials=2, cv_splits=3)
        assert (MODEL_DIR / "density_feature_importance.json").exists()

    def test_model_can_predict(self):
        result = train_density_model_v2(n_trials=2, cv_splits=3)
        import joblib
        model = joblib.load(MODEL_DIR / "density_xgb_model.joblib")
        le = joblib.load(MODEL_DIR / "density_label_encoder.joblib")
        df = pd.read_csv(RAW_DIR / "training_density.csv")
        X, _ = prepare_density_features(df)
        sample = X.head(1)
        pred_encoded = model.predict(sample)
        pred = le.inverse_transform(pred_encoded)
        assert len(pred) == 1
        assert pred[0] in {"LOW", "MEDIUM", "HIGH", "OVERLOADED"}
