"""Tests for ETA model training with XGBoost + Optuna."""
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.aits.ml.train import (
    train_eta_model_v2,
    prepare_eta_features,
    create_preprocessor,
)


RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"
MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
GTFS_DIR = RAW_DIR / "gtfs_transjakarta"


@pytest.fixture(scope="session", autouse=True)
def ensure_training_csv():
    """Ensure the GTFS-derived training_eta.csv exists (old generate_all may overwrite it)."""
    from src.aits.data.build_training_dataset import build_training_eta
    csv_path = RAW_DIR / "training_eta.csv"
    # Check if it's the new format (has from_stop_id column)
    if csv_path.exists():
        df_check = pd.read_csv(csv_path, nrows=1)
        if "from_stop_id" not in df_check.columns:
            print("Re-generating GTFS-derived training_eta.csv (old format detected)...")
            build_training_eta(GTFS_DIR, output_path=csv_path)
    else:
        print("Generating GTFS-derived training_eta.csv...")
        build_training_eta(GTFS_DIR, output_path=csv_path)


class TestPrepareEtaFeatures:
    """Test feature engineering for ETA model."""

    def test_returns_dataframe(self):
        df = pd.read_csv(RAW_DIR / "training_eta.csv")
        X, y = prepare_eta_features(df)
        assert isinstance(X, pd.DataFrame)
        assert isinstance(y, pd.Series)

    def test_no_leakage_features(self):
        df = pd.read_csv(RAW_DIR / "training_eta.csv")
        X, y = prepare_eta_features(df)
        leakage = ["passenger_density_score", "incident_flag", "tap_in_count_15m"]
        for feat in leakage:
            assert feat not in X.columns, f"Leakage feature found: {feat}"

    def test_has_cyclical_features(self):
        df = pd.read_csv(RAW_DIR / "training_eta.csv")
        X, y = prepare_eta_features(df)
        assert "hour_sin" in X.columns
        assert "hour_cos" in X.columns
        assert "dow_sin" in X.columns
        assert "dow_cos" in X.columns

    def test_has_all_expected_features(self):
        df = pd.read_csv(RAW_DIR / "training_eta.csv")
        X, y = prepare_eta_features(df)
        expected = [
            "route_id", "from_stop_id", "to_stop_id", "route_mode",
            "hour_sin", "hour_cos", "dow_sin", "dow_cos",
            "scheduled_travel_seconds", "headway_minutes",
            "rainfall_level", "flood_flag", "temperature_c",
            "historical_incident_rate", "is_rush_hour",
        ]
        for feat in expected:
            assert feat in X.columns, f"Missing feature: {feat}"

    def test_no_identifier_columns(self):
        df = pd.read_csv(RAW_DIR / "training_eta.csv")
        X, y = prepare_eta_features(df)
        assert "trip_id" not in X.columns
        assert "date" not in X.columns
        assert "scheduled_departure" not in X.columns
        assert "scheduled_arrival" not in X.columns

    def test_rows_preserved(self):
        df = pd.read_csv(RAW_DIR / "training_eta.csv")
        X, y = prepare_eta_features(df)
        assert len(X) == len(df)
        assert len(y) == len(df)

    def test_target_is_delay_minutes(self):
        df = pd.read_csv(RAW_DIR / "training_eta.csv")
        X, y = prepare_eta_features(df)
        assert y.name == "delay_minutes"
        assert (y >= 0).all()


class TestCreatePreprocessor:
    """Test sklearn preprocessor construction."""

    def test_returns_column_transformer(self):
        from sklearn.compose import ColumnTransformer
        pp = create_preprocessor()
        assert isinstance(pp, ColumnTransformer)

    def test_has_cat_and_num_transformers(self):
        pp = create_preprocessor()
        names = [name for name, _, _ in pp.transformers]
        assert "cat" in names
        assert "num" in names


class TestTrainEtaModelV2:
    """Integration tests for the full training pipeline."""

    @pytest.fixture(autouse=True)
    def _use_temp_model_dir(self, tmp_path, monkeypatch):
        """Redirect model saving to temp dir so tests don't overwrite production model."""
        monkeypatch.setattr("src.aits.ml.train.MODEL_DIR", tmp_path)

    def test_returns_dict_with_expected_keys(self):
        result = train_eta_model_v2(n_trials=2, cv_splits=3)
        assert "best_mae" in result
        assert "best_params" in result
        assert "cv_mae_mean" in result
        assert "cv_mae_std" in result
        assert "test_mae" in result
        assert "test_rmse" in result
        assert "test_r2" in result
        assert "test_median_ae" in result
        assert "within_1min_pct" in result
        assert "within_2min_pct" in result
        assert "within_3min_pct" in result
        assert "n_rows" in result
        assert "n_features" in result

    def test_mae_is_reasonable(self):
        result = train_eta_model_v2(n_trials=2, cv_splits=3)
        assert 0.0 < result["test_mae"] < 10.0, f"MAE out of range: {result['test_mae']}"

    def test_r2_is_positive(self):
        result = train_eta_model_v2(n_trials=2, cv_splits=3)
        assert result["test_r2"] > 0, f"R2 should be positive: {result['test_r2']}"

    def test_model_saved_to_disk(self):
        result = train_eta_model_v2(n_trials=2, cv_splits=3)
        model_path = MODEL_DIR / "eta_xgb_model.joblib"
        assert model_path.exists(), "Model file not saved"

    def test_metrics_saved_to_disk(self):
        result = train_eta_model_v2(n_trials=2, cv_splits=3)
        metrics_path = MODEL_DIR / "eta_metrics.json"
        assert metrics_path.exists(), "Metrics file not saved"
        with open(metrics_path) as f:
            loaded = json.load(f)
        assert "test_mae" in loaded

    def test_feature_importance_saved(self):
        result = train_eta_model_v2(n_trials=2, cv_splits=3)
        fi_path = MODEL_DIR / "eta_feature_importance.json"
        assert fi_path.exists(), "Feature importance file not saved"

    def test_model_can_predict(self):
        result = train_eta_model_v2(n_trials=2, cv_splits=3)
        import joblib
        model = joblib.load(MODEL_DIR / "eta_xgb_model.joblib")
        df = pd.read_csv(RAW_DIR / "training_eta.csv")
        X, _ = prepare_eta_features(df)
        sample = X.head(1)
        pred = model.predict(sample)
        assert len(pred) == 1
        assert pred[0] >= 0

    def test_n_trials_parameter_works(self):
        result = train_eta_model_v2(n_trials=3, cv_splits=3)
        assert result["best_params"] is not None
        assert isinstance(result["best_params"], dict)
