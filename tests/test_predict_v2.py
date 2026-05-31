"""Tests for predict.py v2 — FeatureBuilder + ModelRegistry.

TDD: These tests define the contract. Implementation must make them pass.
Fast unit tests only — no full training, no e2e pipeline.
"""
from __future__ import annotations

import math
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import TargetEncoder
from xgboost import XGBRegressor, XGBClassifier


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_eta_features():
    """Minimal valid input dict for ETA prediction."""
    return {
        "route_id": "TJ_01",
        "from_stop_id": "TJ_STOP_A",
        "to_stop_id": "TJ_STOP_B",
        "route_mode": "TRANSJAKARTA",
        "scheduled_travel_seconds": 600,
        "headway_minutes": 8.0,
        "hour": 8,
        "day_of_week": 1,
        "rainfall_level": 1,
        "flood_flag": 0,
        "temperature_c": 28,
        "historical_incident_rate": 0.05,
    }


@pytest.fixture
def sample_density_features():
    """Minimal valid input dict for density prediction."""
    return {
        "from_stop_id": "TJ_STOP_A",
        "route_id": "TJ_01",
        "headway_minutes": 8.0,
        "vehicle_capacity": 80,
        "hour": 8,
        "day_of_week": 1,
        "rainfall_level": 1,
        "flood_flag": 0,
        "event_flag": 0,
    }


@pytest.fixture
def tiny_eta_pipeline(tmp_path):
    """Create a tiny XGBoost Pipeline that mimics the trained ETA model."""
    cat_features = ["route_id", "from_stop_id", "to_stop_id", "route_mode"]
    num_features = [
        "scheduled_travel_seconds", "headway_minutes",
        "rainfall_level", "flood_flag", "temperature_c",
        "historical_incident_rate", "is_rush_hour",
        "hour_sin", "hour_cos", "dow_sin", "dow_cos",
    ]
    preprocessor = ColumnTransformer([
        ("cat", TargetEncoder(smooth="auto"), cat_features),
        ("num", "passthrough", num_features),
    ])
    model = XGBRegressor(n_estimators=5, max_depth=2, random_state=42, verbosity=0)
    pipe = Pipeline([("preprocessor", preprocessor), ("model", model)])

    # Train on dummy data
    n = 50
    rng = np.random.RandomState(42)
    df = pd.DataFrame({
        "route_id": rng.choice(["TJ_01", "TJ_02"], n),
        "from_stop_id": rng.choice(["A", "B", "C"], n),
        "to_stop_id": rng.choice(["X", "Y", "Z"], n),
        "route_mode": rng.choice(["TRANSJAKARTA", "MIKROTRANS"], n),
        "scheduled_travel_seconds": rng.randint(200, 1200, n),
        "headway_minutes": rng.uniform(4, 15, n),
        "rainfall_level": rng.randint(0, 4, n),
        "flood_flag": rng.randint(0, 2, n),
        "temperature_c": rng.randint(24, 35, n),
        "historical_incident_rate": rng.uniform(0, 0.3, n),
        "is_rush_hour": rng.randint(0, 2, n),
        "hour_sin": np.sin(2 * np.pi * rng.randint(0, 24, n) / 24),
        "hour_cos": np.cos(2 * np.pi * rng.randint(0, 24, n) / 24),
        "dow_sin": np.sin(2 * np.pi * rng.randint(0, 7, n) / 7),
        "dow_cos": np.cos(2 * np.pi * rng.randint(0, 7, n) / 7),
    })
    y = rng.uniform(0, 5, n).astype(np.float32)
    pipe.fit(df, y)

    path = tmp_path / "eta_xgb_model.joblib"
    joblib.dump(pipe, path)
    return path


@pytest.fixture
def tiny_density_pipeline(tmp_path):
    """Create a tiny XGBoost Pipeline that mimics the trained density model."""
    from sklearn.preprocessing import LabelEncoder

    cat_features = ["from_stop_id", "route_id"]
    num_features = [
        "headway_minutes", "vehicle_capacity",
        "hour", "day_of_week", "is_rush_hour",
        "rainfall_level", "flood_flag", "event_flag",
    ]
    preprocessor = ColumnTransformer([
        ("cat", TargetEncoder(smooth="auto"), cat_features),
        ("num", "passthrough", num_features),
    ])
    model = XGBClassifier(
        n_estimators=5, max_depth=2, random_state=42, verbosity=0,
        objective="multi:softprob", num_class=4,
    )
    pipe = Pipeline([("preprocessor", preprocessor), ("model", model)])

    n = 50
    rng = np.random.RandomState(42)
    df = pd.DataFrame({
        "from_stop_id": rng.choice(["A", "B", "C"], n),
        "route_id": rng.choice(["TJ_01", "TJ_02"], n),
        "headway_minutes": rng.uniform(4, 15, n),
        "vehicle_capacity": rng.choice([12, 80, 1200], n),
        "hour": rng.randint(0, 24, n),
        "day_of_week": rng.randint(0, 7, n),
        "is_rush_hour": rng.randint(0, 2, n),
        "rainfall_level": rng.randint(0, 4, n),
        "flood_flag": rng.randint(0, 2, n),
        "event_flag": rng.randint(0, 2, n),
    })
    labels = rng.choice(["LOW", "MEDIUM", "HIGH", "OVERLOADED"], n)
    le = LabelEncoder()
    y = le.fit_transform(labels)
    pipe.fit(df, y)

    pipe_path = tmp_path / "density_xgb_model.joblib"
    le_path = tmp_path / "density_label_encoder.joblib"
    joblib.dump(pipe, pipe_path)
    joblib.dump(le, le_path)
    return pipe_path, le_path


# ---------------------------------------------------------------------------
# FeatureBuilder: ETA feature column names
# ---------------------------------------------------------------------------

class TestEtaFeatureColumns:
    """Verify FeatureBuilder produces columns that match training pipeline."""

    def test_eta_features_column_names_match_training(self, sample_eta_features):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        df = fb.build_eta_features(**sample_eta_features)

        expected_cats = {"route_id", "from_stop_id", "to_stop_id", "route_mode"}
        expected_nums = {
            "scheduled_travel_seconds", "headway_minutes",
            "rainfall_level", "flood_flag", "temperature_c",
            "historical_incident_rate", "is_rush_hour",
        }
        expected_cyclical = {"hour_sin", "hour_cos", "dow_sin", "dow_cos"}
        all_expected = expected_cats | expected_nums | expected_cyclical

        assert set(df.columns) == all_expected, (
            f"Missing: {all_expected - set(df.columns)}, "
            f"Extra: {set(df.columns) - all_expected}"
        )

    def test_eta_features_single_row(self, sample_eta_features):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        df = fb.build_eta_features(**sample_eta_features)
        assert len(df) == 1


# ---------------------------------------------------------------------------
# FeatureBuilder: Density feature column names
# ---------------------------------------------------------------------------

class TestDensityFeatureColumns:
    """Verify density feature columns match training pipeline."""

    def test_density_features_column_names_match_training(self, sample_density_features):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        df = fb.build_density_features(**sample_density_features)

        expected_cats = {"from_stop_id", "route_id"}
        expected_nums = {
            "headway_minutes", "vehicle_capacity",
            "hour", "day_of_week", "is_rush_hour",
            "rainfall_level", "flood_flag", "event_flag",
        }
        all_expected = expected_cats | expected_nums
        assert set(df.columns) == all_expected

    def test_density_features_single_row(self, sample_density_features):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        df = fb.build_density_features(**sample_density_features)
        assert len(df) == 1


# ---------------------------------------------------------------------------
# FeatureBuilder: Cyclical encoding
# ---------------------------------------------------------------------------

class TestCyclicalEncoding:
    def test_hour_sin_cos_values(self):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        df = fb.build_eta_features(
            route_id="TJ_01", from_stop_id="A", to_stop_id="B",
            route_mode="TRANSJAKARTA", scheduled_travel_seconds=600,
            headway_minutes=8.0, hour=6, day_of_week=0,
            rainfall_level=0, flood_flag=0, temperature_c=28,
            historical_incident_rate=0.0,
        )
        expected_sin = math.sin(2 * math.pi * 6 / 24)
        expected_cos = math.cos(2 * math.pi * 6 / 24)
        assert abs(df["hour_sin"].iloc[0] - expected_sin) < 1e-6
        assert abs(df["hour_cos"].iloc[0] - expected_cos) < 1e-6

    def test_dow_sin_cos_values(self):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        df = fb.build_eta_features(
            route_id="TJ_01", from_stop_id="A", to_stop_id="B",
            route_mode="TRANSJAKARTA", scheduled_travel_seconds=600,
            headway_minutes=8.0, hour=8, day_of_week=3,
            rainfall_level=0, flood_flag=0, temperature_c=28,
            historical_incident_rate=0.0,
        )
        expected_sin = math.sin(2 * math.pi * 3 / 7)
        expected_cos = math.cos(2 * math.pi * 3 / 7)
        assert abs(df["dow_sin"].iloc[0] - expected_sin) < 1e-6
        assert abs(df["dow_cos"].iloc[0] - expected_cos) < 1e-6


# ---------------------------------------------------------------------------
# FeatureBuilder: is_rush_hour
# ---------------------------------------------------------------------------

class TestRushHour:
    def test_morning_rush(self):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        for h in [7, 8, 9]:
            df = fb.build_eta_features(
                route_id="TJ_01", from_stop_id="A", to_stop_id="B",
                route_mode="TRANSJAKARTA", scheduled_travel_seconds=600,
                headway_minutes=8.0, hour=h, day_of_week=1,
                rainfall_level=0, flood_flag=0, temperature_c=28,
                historical_incident_rate=0.0,
            )
            assert df["is_rush_hour"].iloc[0] == 1, f"hour={h} should be rush"

    def test_evening_rush(self):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        for h in [16, 17, 18, 19]:
            df = fb.build_eta_features(
                route_id="TJ_01", from_stop_id="A", to_stop_id="B",
                route_mode="TRANSJAKARTA", scheduled_travel_seconds=600,
                headway_minutes=8.0, hour=h, day_of_week=1,
                rainfall_level=0, flood_flag=0, temperature_c=28,
                historical_incident_rate=0.0,
            )
            assert df["is_rush_hour"].iloc[0] == 1, f"hour={h} should be rush"

    def test_non_rush(self):
        from src.aits.ml.predict import FeatureBuilder
        fb = FeatureBuilder()
        for h in [12, 22, 3]:
            df = fb.build_eta_features(
                route_id="TJ_01", from_stop_id="A", to_stop_id="B",
                route_mode="TRANSJAKARTA", scheduled_travel_seconds=600,
                headway_minutes=8.0, hour=h, day_of_week=1,
                rainfall_level=0, flood_flag=0, temperature_c=28,
                historical_incident_rate=0.0,
            )
            assert df["is_rush_hour"].iloc[0] == 0, f"hour={h} should not be rush"


# ---------------------------------------------------------------------------
# ModelRegistry: ETA prediction with tiny model
# ---------------------------------------------------------------------------

class TestEtaPrediction:
    def test_returns_valid_result(self, tiny_eta_pipeline, sample_eta_features):
        from src.aits.ml.predict import ModelRegistry, EtaPrediction
        registry = ModelRegistry(model_dir=tiny_eta_pipeline.parent)
        result = registry.predict_eta_delay(sample_eta_features)
        assert isinstance(result, EtaPrediction)
        assert result.predicted_delay_minutes >= 0.0
        assert result.predicted_eta_minutes > 0.0
        assert 0.0 <= result.confidence_score <= 1.0

    def test_delay_clamped_non_negative(self, tiny_eta_pipeline, sample_eta_features):
        from src.aits.ml.predict import ModelRegistry
        registry = ModelRegistry(model_dir=tiny_eta_pipeline.parent)
        result = registry.predict_eta_delay(sample_eta_features)
        assert result.predicted_delay_minutes >= 0.0

    def test_eta_equals_scheduled_plus_delay(self, tiny_eta_pipeline, sample_eta_features):
        from src.aits.ml.predict import ModelRegistry
        registry = ModelRegistry(model_dir=tiny_eta_pipeline.parent)
        result = registry.predict_eta_delay(sample_eta_features)
        scheduled_min = sample_eta_features["scheduled_travel_seconds"] / 60.0
        expected_eta = scheduled_min + result.predicted_delay_minutes
        assert abs(result.predicted_eta_minutes - expected_eta) < 0.01


# ---------------------------------------------------------------------------
# ModelRegistry: Density prediction with tiny model
# ---------------------------------------------------------------------------

class TestDensityPrediction:
    def test_returns_valid_result(self, tiny_density_pipeline, sample_density_features):
        from src.aits.ml.predict import ModelRegistry, DensityPrediction
        pipe_path, le_path = tiny_density_pipeline
        registry = ModelRegistry(
            model_dir=pipe_path.parent,
            density_label_encoder_path=le_path,
        )
        result = registry.predict_density(sample_density_features)
        assert isinstance(result, DensityPrediction)
        assert result.density_level in {"LOW", "MEDIUM", "HIGH", "OVERLOADED"}
        assert 0.0 <= result.confidence_score <= 1.0

    def test_confidence_from_proba(self, tiny_density_pipeline, sample_density_features):
        from src.aits.ml.predict import ModelRegistry
        pipe_path, le_path = tiny_density_pipeline
        registry = ModelRegistry(
            model_dir=pipe_path.parent,
            density_label_encoder_path=le_path,
        )
        result = registry.predict_density(sample_density_features)
        # With predict_proba available, confidence should be > 0.25 (random for 4 classes)
        assert result.confidence_score >= 0.25


# ---------------------------------------------------------------------------
# ModelRegistry: Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_missing_eta_model_raises(self, tmp_path):
        from src.aits.ml.predict import ModelRegistry
        registry = ModelRegistry(model_dir=tmp_path)
        with pytest.raises(FileNotFoundError, match="ETA model not found"):
            registry.predict_eta_delay({
                "route_id": "TJ_01", "from_stop_id": "A", "to_stop_id": "B",
                "route_mode": "TRANSJAKARTA", "scheduled_travel_seconds": 600,
                "headway_minutes": 8.0, "hour": 8, "day_of_week": 1,
                "rainfall_level": 0, "flood_flag": 0, "temperature_c": 28,
                "historical_incident_rate": 0.0,
            })

    def test_missing_density_model_returns_default(self, tmp_path, sample_density_features):
        from src.aits.ml.predict import ModelRegistry, DensityPrediction
        registry = ModelRegistry(model_dir=tmp_path)
        result = registry.predict_density(sample_density_features)
        assert isinstance(result, DensityPrediction)
        assert result.density_level == "MEDIUM"
        assert result.confidence_score == 0.0


# ---------------------------------------------------------------------------
# Service contract: dict output keys
# ---------------------------------------------------------------------------

class TestServiceContract:
    def test_eta_output_has_expected_keys(self, tiny_eta_pipeline, sample_eta_features):
        from dataclasses import asdict
        from src.aits.ml.predict import ModelRegistry
        registry = ModelRegistry(model_dir=tiny_eta_pipeline.parent)
        result = registry.predict_eta_delay(sample_eta_features)
        d = asdict(result)
        assert set(d.keys()) == {"predicted_delay_minutes", "predicted_eta_minutes", "confidence_score"}

    def test_density_output_has_expected_keys(self, tiny_density_pipeline, sample_density_features):
        from dataclasses import asdict
        from src.aits.ml.predict import ModelRegistry
        pipe_path, le_path = tiny_density_pipeline
        registry = ModelRegistry(
            model_dir=pipe_path.parent,
            density_label_encoder_path=le_path,
        )
        result = registry.predict_density(sample_density_features)
        d = asdict(result)
        assert set(d.keys()) == {"density_level", "load_factor_estimate", "confidence_score"}
