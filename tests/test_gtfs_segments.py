"""Tests for gtfs_to_segments.py — Extract segment skeleton from GTFS."""
import pandas as pd
import pytest
from pathlib import Path
from datetime import time

from src.aits.data.gtfs_to_segments import (
    extract_segments,
    compute_scheduled_travel_seconds,
    get_headway_for_time,
    build_segment_row,
)

GTFS_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "gtfs_transjakarta"


class TestComputeScheduledTravelSeconds:
    """Test scheduled travel time computation between two stops."""

    def test_simple_difference(self):
        dep = time(5, 0, 10)
        arr = time(5, 1, 31)
        result = compute_scheduled_travel_seconds(dep, arr)
        assert result == 81  # 1 min 21 sec

    def test_same_time_returns_zero(self):
        t = time(10, 30, 0)
        result = compute_scheduled_travel_seconds(t, t)
        assert result == 0

    def test_longer_segment(self):
        dep = time(6, 0, 0)
        arr = time(6, 5, 30)
        result = compute_scheduled_travel_seconds(dep, arr)
        assert result == 330  # 5 min 30 sec


class TestGetHeadwayForTime:
    """Test headway lookup from GTFS frequencies."""

    def test_returns_numeric_headway(self, sample_frequencies):
        result = get_headway_for_time(sample_frequencies, "trip_1", time(8, 0))
        assert isinstance(result, (int, float))
        assert result > 0

    def test_returns_default_when_no_match(self, sample_frequencies):
        result = get_headway_for_time(sample_frequencies, "nonexistent_trip", time(8, 0))
        assert result == 360  # default 6 min = 360 seconds


class TestBuildSegmentRow:
    """Test single segment row construction."""

    def test_row_has_required_columns(self, sample_segment_input):
        row = build_segment_row(**sample_segment_input)
        required = [
            "trip_id", "route_id", "direction",
            "from_stop_id", "to_stop_id", "stop_sequence",
            "scheduled_departure", "scheduled_arrival",
            "scheduled_travel_seconds", "hour", "day_of_week",
            "headway_minutes", "route_mode",
        ]
        for col in required:
            assert col in row, f"Missing column: {col}"

    def test_travel_seconds_computed_correctly(self, sample_segment_input):
        row = build_segment_row(**sample_segment_input)
        assert row["scheduled_travel_seconds"] == 81

    def test_hour_extracted_from_departure(self, sample_segment_input):
        row = build_segment_row(**sample_segment_input)
        assert row["hour"] == 5


class TestExtractSegments:
    """Integration test: extract segments from real GTFS data."""

    def test_returns_dataframe(self, gtfs_segments):
        assert isinstance(gtfs_segments, pd.DataFrame)

    def test_has_minimum_rows(self, gtfs_segments):
        assert len(gtfs_segments) >= 1000, f"Expected >=1000 segments, got {len(gtfs_segments)}"

    def test_has_all_required_columns(self, gtfs_segments):
        required = [
            "trip_id", "route_id", "direction",
            "from_stop_id", "to_stop_id", "stop_sequence",
            "scheduled_departure", "scheduled_arrival",
            "scheduled_travel_seconds", "hour", "day_of_week",
            "headway_minutes", "route_mode",
        ]
        for col in required:
            assert col in gtfs_segments.columns, f"Missing column: {col}"

    def test_no_negative_travel_times(self, gtfs_segments):
        assert (gtfs_segments["scheduled_travel_seconds"] >= 0).all()

    def test_travel_seconds_are_reasonable(self, gtfs_segments):
        reasonable = gtfs_segments["scheduled_travel_seconds"].between(10, 1800)
        assert reasonable.mean() > 0.9, "More than 10% of segments have unreasonable travel times"

    def test_hour_in_valid_range(self, gtfs_segments):
        assert gtfs_segments["hour"].between(0, 23).all()

    def test_day_of_week_in_valid_range(self, gtfs_segments):
        assert gtfs_segments["day_of_week"].between(0, 6).all()

    def test_headway_positive(self, gtfs_segments):
        assert (gtfs_segments["headway_minutes"] > 0).all()

    def test_route_mode_is_string(self, gtfs_segments):
        assert gtfs_segments["route_mode"].dtype == object


# --- Fixtures ---


@pytest.fixture(scope="session")
def gtfs_segments():
    """Cache extracted segments for all integration tests (expensive operation)."""
    return extract_segments(GTFS_DIR)


@pytest.fixture
def sample_frequencies():
    """Sample GTFS frequencies data."""
    return pd.DataFrame({
        "trip_id": ["trip_1", "trip_1", "trip_2"],
        "start_time": ["05:00:00", "10:00:00", "06:00:00"],
        "end_time": ["09:00:00", "22:00:00", "10:00:00"],
        "headway_secs": [360, 600, 240],
    })


@pytest.fixture
def sample_segment_input():
    """Sample input for build_segment_row."""
    return {
        "trip_id": "JAK.33-L01",
        "route_id": "33",
        "direction": 0,
        "from_stop_id": "B02998P",
        "to_stop_id": "B05314P",
        "stop_sequence": 0,
        "scheduled_departure": time(5, 0, 10),
        "scheduled_arrival": time(5, 1, 31),
        "headway_minutes": 6,
        "route_mode": "TRANSJAKARTA",
    }
