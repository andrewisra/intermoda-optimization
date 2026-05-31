"""Tests for build_training_dataset.py — Orchestrates all 3 layers."""
import pandas as pd
import pytest
from pathlib import Path
from datetime import date, time

from src.aits.data.build_training_dataset import (
    build_training_eta,
    attach_weather,
    attach_delay,
    add_date_to_segments,
)

GTFS_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "gtfs_transjakarta"


@pytest.fixture(scope="session")
def training_eta_df():
    """Cache the full training ETA dataset (expensive to build)."""
    return build_training_eta(GTFS_DIR)


class TestAddDateToSegments:
    """Test date assignment to GTFS segments."""

    def test_adds_date_column(self):
        seg = pd.DataFrame([{
            "trip_id": "T1", "route_id": "R1", "direction": 0,
            "from_stop_id": "S1", "to_stop_id": "S2", "stop_sequence": 0,
            "scheduled_departure": "08:00:00", "scheduled_arrival": "08:05:00",
            "scheduled_travel_seconds": 300, "hour": 8, "day_of_week": 0,
            "headway_minutes": 6.0, "route_mode": "TRANSJAKARTA",
        }])
        result = add_date_to_segments(seg)
        assert "date" in result.columns
        assert isinstance(result["date"].iloc[0], date)

    def test_preserves_all_columns(self):
        seg = pd.DataFrame([{
            "trip_id": "T1", "route_id": "R1", "direction": 0,
            "from_stop_id": "S1", "to_stop_id": "S2", "stop_sequence": 0,
            "scheduled_departure": "08:00:00", "scheduled_arrival": "08:05:00",
            "scheduled_travel_seconds": 300, "hour": 8, "day_of_week": 0,
            "headway_minutes": 6.0, "route_mode": "TRANSJAKARTA",
        }])
        result = add_date_to_segments(seg)
        assert "trip_id" in result.columns
        assert "route_mode" in result.columns


class TestAttachWeather:
    """Test weather context attachment."""

    def test_adds_weather_columns(self):
        seg = pd.DataFrame([{
            "date": date(2024, 1, 15),
            "hour": 10, "route_mode": "TRANSJAKARTA",
            "scheduled_travel_seconds": 300,
        }])
        result = attach_weather(seg)
        assert "rainfall_level" in result.columns
        assert "flood_flag" in result.columns
        assert "temperature_c" in result.columns

    def test_weather_values_in_valid_range(self):
        seg = pd.DataFrame([{
            "date": date(2024, 1, 15),
            "hour": 10, "route_mode": "TRANSJAKARTA",
            "scheduled_travel_seconds": 300,
        } for _ in range(50)])
        result = attach_weather(seg)
        assert result["rainfall_level"].between(0, 3).all()
        assert result["flood_flag"].isin([0, 1]).all()
        assert result["temperature_c"].between(24, 35).all()


class TestAttachDelay:
    """Test delay label generation."""

    def test_adds_delay_minutes_column(self):
        seg = pd.DataFrame([{
            "scheduled_travel_seconds": 300,
            "route_mode": "TRANSJAKARTA",
            "hour": 10,
            "rainfall_level": 0,
            "flood_flag": 0,
        }])
        result = attach_delay(seg)
        assert "delay_minutes" in result.columns
        assert result["delay_minutes"].iloc[0] >= 0

    def test_adds_historical_incident_rate(self):
        seg = pd.DataFrame([{
            "scheduled_travel_seconds": 300,
            "route_mode": "TRANSJAKARTA",
            "hour": 10,
            "rainfall_level": 0,
            "flood_flag": 0,
        }])
        result = attach_delay(seg)
        assert "historical_incident_rate" in result.columns
        assert 0 <= result["historical_incident_rate"].iloc[0] <= 1


class TestBuildTrainingEta:
    """Integration test: build the full training dataset."""

    def test_returns_dataframe(self, training_eta_df):
        assert isinstance(training_eta_df, pd.DataFrame)

    def test_has_minimum_rows(self, training_eta_df):
        assert len(training_eta_df) >= 1000

    def test_has_all_required_columns(self, training_eta_df):
        required = [
            "trip_id", "route_id", "direction",
            "from_stop_id", "to_stop_id", "stop_sequence",
            "scheduled_departure", "scheduled_arrival",
            "scheduled_travel_seconds", "hour", "day_of_week",
            "headway_minutes", "route_mode",
            "date", "rainfall_level", "flood_flag", "temperature_c",
            "delay_minutes", "historical_incident_rate",
        ]
        for col in required:
            assert col in training_eta_df.columns, f"Missing column: {col}"

    def test_delay_minutes_non_negative(self, training_eta_df):
        assert (training_eta_df["delay_minutes"] >= 0).all()

    def test_delay_minutes_has_variance(self, training_eta_df):
        assert training_eta_df["delay_minutes"].std() > 0

    def test_delay_minutes_reasonable_range(self, training_eta_df):
        assert training_eta_df["delay_minutes"].quantile(0.99) <= 20

    def test_no_leakage_features(self, training_eta_df):
        leakage_features = ["passenger_density_score", "incident_flag", "tap_in_count_15m"]
        for feat in leakage_features:
            assert feat not in training_eta_df.columns, f"Leakage feature found: {feat}"

    def test_has_all_pre_trip_features(self, training_eta_df):
        pre_trip = [
            "route_id", "from_stop_id", "to_stop_id",
            "hour", "day_of_week", "scheduled_travel_seconds",
            "headway_minutes", "route_mode", "rainfall_level", "flood_flag",
            "is_rush_hour", "historical_incident_rate",
        ]
        for feat in pre_trip:
            assert feat in training_eta_df.columns, f"Missing pre-trip feature: {feat}"

    def test_can_save_to_csv(self, training_eta_df, tmp_path):
        out_path = tmp_path / "training_eta.csv"
        training_eta_df.to_csv(out_path, index=False)
        loaded = pd.read_csv(out_path)
        assert len(loaded) == len(training_eta_df)
        assert "delay_minutes" in loaded.columns
