"""Tests for density dataset builder — no data leakage, stochastic labels."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.aits.data.build_density_dataset import build_density_dataset

GTFS_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "gtfs_transjakarta"


class TestBuildDensityDataset:
    def test_returns_dataframe(self):
        df = build_density_dataset(GTFS_DIR)
        assert isinstance(df, pd.DataFrame)

    def test_has_minimum_rows(self):
        df = build_density_dataset(GTFS_DIR)
        assert len(df) >= 1000

    def test_has_required_columns(self):
        df = build_density_dataset(GTFS_DIR)
        required = [
            "from_stop_id", "route_id", "headway_minutes", "vehicle_capacity",
            "hour", "day_of_week", "is_rush_hour",
            "rainfall_level", "flood_flag", "event_flag",
            "routes_through_stop", "is_terminal", "route_demand_factor",
            "density_level",
        ]
        for col in required:
            assert col in df.columns, f"Missing column: {col}"

    def test_no_leakage_tap_in(self):
        df = build_density_dataset(GTFS_DIR)
        assert "tap_in_count_15m" not in df.columns

    def test_no_leakage_load_factor(self):
        df = build_density_dataset(GTFS_DIR)
        assert "load_factor" not in df.columns

    def test_no_leakage_incident_flag(self):
        df = build_density_dataset(GTFS_DIR)
        assert "incident_flag" not in df.columns

    def test_density_levels_valid(self):
        df = build_density_dataset(GTFS_DIR)
        valid = {"LOW", "MEDIUM", "HIGH", "OVERLOADED"}
        assert set(df["density_level"].unique()).issubset(valid)

    def test_density_balanced_distribution(self):
        df = build_density_dataset(GTFS_DIR)
        dist = df["density_level"].value_counts(normalize=True)
        # No single class should dominate > 80% (realistic transit distribution)
        assert dist.max() < 0.80, f"Dominant class too large: {dist.max():.2%}"
        # All 4 classes should be present
        assert len(dist) == 4, f"Expected 4 classes, got {len(dist)}: {list(dist.index)}"

    def test_connectivity_varies(self):
        df = build_density_dataset(GTFS_DIR)
        assert df["routes_through_stop"].nunique() > 1, "Connectivity has no variance"

    def test_connectivity_range(self):
        df = build_density_dataset(GTFS_DIR)
        assert df["routes_through_stop"].min() >= 1
        assert df["routes_through_stop"].max() <= 20

    def test_is_terminal_binary(self):
        df = build_density_dataset(GTFS_DIR)
        assert set(df["is_terminal"].unique()).issubset({0, 1})

    def test_has_terminal_stops(self):
        df = build_density_dataset(GTFS_DIR)
        n_terminal = (df["is_terminal"] == 1).sum()
        assert n_terminal > 0, "No terminal stops detected"

    def test_route_demand_factor_range(self):
        df = build_density_dataset(GTFS_DIR)
        assert df["route_demand_factor"].min() >= 0.7
        assert df["route_demand_factor"].max() <= 1.3

    def test_route_demand_factor_varies(self):
        df = build_density_dataset(GTFS_DIR)
        assert df["route_demand_factor"].nunique() > 1, "Route demand factor has no variance"

    def test_labels_stochastic(self):
        """Poisson noise means same features → different labels on different runs."""
        import src.aits.data.build_density_dataset as mod
        # Use parameters near LOW/MEDIUM boundary (load_factor ≈ 0.45)
        # base_demand=55, conn_mult=0.7, non-rush → expected=38.5, Poisson(38.5)/80 ≈ 0.48
        # This should produce BOTH LOW and MEDIUM labels
        rng1 = np.random.default_rng(0)
        rng2 = np.random.default_rng(99)
        labels_1 = [mod.generate_density_label(55, 12, 0, 0, 0, 80, 1, rng=rng1) for _ in range(200)]
        labels_2 = [mod.generate_density_label(55, 12, 0, 0, 0, 80, 1, rng=rng2) for _ in range(200)]
        # At least some labels should differ (Poisson noise)
        assert labels_1 != labels_2, "Labels are deterministic — Poisson noise not working"

    def test_can_save_to_csv(self, tmp_path):
        df = build_density_dataset(GTFS_DIR)
        out = tmp_path / "test.csv"
        df.to_csv(out, index=False)
        loaded = pd.read_csv(out)
        assert len(loaded) == len(df)
