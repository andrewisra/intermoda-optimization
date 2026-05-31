"""Build the ETA training dataset by orchestrating 3 layers:
1. GTFS segment skeleton
2. Weather/flood context
3. Calibrated synthetic delay labels

No data leakage: only pre-trip features are included.
"""
from __future__ import annotations

import random
from pathlib import Path
from datetime import date, time

import numpy as np
import pandas as pd

from src.aits.data.gtfs_to_segments import extract_segments
from src.aits.data.weather_provider import get_weather_synthetic, assign_date, WET_MONTHS, DRY_MONTHS
from src.aits.data.delay_generator import generate_delay, get_incident_rate


def add_date_to_segments(segments: pd.DataFrame) -> pd.DataFrame:
    """Assign a synthetic date to each segment based on its day_of_week and season."""
    df = segments.copy()
    dates = []
    for _, row in df.iterrows():
        dow = int(row["day_of_week"])
        if dow in [5, 6]:  # weekend → any season
            month_range = list(WET_MONTHS | DRY_MONTHS)
        else:
            # weekday: alternate wet/dry to get weather variety
            month_range = list(WET_MONTHS) if hash(str(row["trip_id"])) % 2 == 0 else list(DRY_MONTHS)
        dates.append(assign_date(dow, month_range))
    df["date"] = dates
    return df


def attach_weather(segments: pd.DataFrame) -> pd.DataFrame:
    """Attach synthetic weather context to each segment."""
    df = segments.copy()
    rainfall = []
    flood = []
    temp = []
    for _, row in df.iterrows():
        d = row["date"]
        t = time(int(row["hour"]), 0)
        w = get_weather_synthetic(d, t)
        rainfall.append(w["rainfall_level"])
        flood.append(w["flood_flag"])
        temp.append(w["temperature_c"])
    df["rainfall_level"] = rainfall
    df["flood_flag"] = flood
    df["temperature_c"] = temp
    return df


def attach_delay(segments: pd.DataFrame) -> pd.DataFrame:
    """Generate calibrated synthetic delay labels."""
    df = segments.copy()
    delays = []
    incident_rates = []
    for _, row in df.iterrows():
        d = generate_delay(
            scheduled_travel_seconds=int(row["scheduled_travel_seconds"]),
            route_mode=row["route_mode"],
            hour=int(row["hour"]),
            rainfall_level=int(row["rainfall_level"]),
            flood_flag=int(row["flood_flag"]),
        )
        delays.append(d)
        ir = get_incident_rate(row["route_mode"], int(row["hour"]), int(row["rainfall_level"]))
        incident_rates.append(ir)
    df["delay_minutes"] = delays
    df["historical_incident_rate"] = incident_rates
    return df


def build_training_eta(
    gtfs_dir: Path,
    output_path: Path | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Build the complete ETA training dataset.

    Steps:
    1. Extract GTFS segment skeleton
    2. Add synthetic dates
    3. Attach weather context
    4. Generate calibrated delay labels
    5. Add derived features (is_rush_hour, historical_incident_rate)
    6. No leakage features (no passenger_density_score, no incident_flag, no tap_in)

    Returns the final DataFrame. Optionally saves to CSV.
    Always regenerates from GTFS for determinism (takes ~30s).
    """
    # Seed all RNGs for reproducibility
    random.seed(42)
    np.random.seed(42)

    # Layer 1: GTFS segment skeleton
    segments = extract_segments(gtfs_dir)

    # Add dates for weather joining
    segments = add_date_to_segments(segments)

    # Layer 2: Weather/flood context
    segments = attach_weather(segments)

    # Layer 3: Calibrated synthetic delay + incident rate
    segments = attach_delay(segments)

    # Derived features
    segments["is_rush_hour"] = segments["hour"].apply(
        lambda h: 1 if 7 <= h <= 9 or 16 <= h <= 19 else 0
    )

    # Ensure no leakage features
    leakage = ["passenger_density_score", "incident_flag", "tap_in_count_15m"]
    for col in leakage:
        if col in segments.columns:
            segments.drop(columns=[col], inplace=True)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        segments.to_csv(output_path, index=False)

    return segments
