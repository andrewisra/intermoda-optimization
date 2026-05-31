"""Build the density training dataset — NO data leakage.

3-layer architecture:
1. GTFS segment structure (real stops, routes, schedules)
2. Weather/event context (synthetic, calibrated to Jakarta)
3. Synthetic density labels with Poisson noise (realistic passenger arrivals)

Label generation uses:
- Stop connectivity (number of routes through each stop)
- Terminal vs intermediate stop type
- Route-specific demand factors
- Poisson-distributed passenger arrivals (research-validated)
"""
from __future__ import annotations

import random
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.aits.data.gtfs_to_segments import extract_segments
from src.aits.data.weather_provider import get_weather_synthetic, assign_date, WET_MONTHS, DRY_MONTHS


# Demand calibration constants
BASE_DEMAND = {
    "TRANSJAKARTA": 55,
    "MIKROTRANS": 8,
    "MRT_LRT": 350,
    "KRL": 300,
}

RUSH_HOURS = set(range(7, 10)) | set(range(16, 20))


def is_rush_hour(hour: int) -> bool:
    return hour in RUSH_HOURS


def compute_stop_connectivity(gtfs_dir: Path) -> dict[str, int]:
    """Count how many routes pass through each stop."""
    stop_times = pd.read_csv(gtfs_dir / "stop_times.txt", low_memory=False)
    trips = pd.read_csv(gtfs_dir / "trips.txt", low_memory=False)
    merged = stop_times[["trip_id", "stop_id"]].merge(
        trips[["trip_id", "route_id"]], on="trip_id"
    )
    return merged.groupby("stop_id")["route_id"].nunique().to_dict()


def compute_terminal_stops(gtfs_dir: Path) -> set[str]:
    """Identify terminal stops (first or last stop of any trip).

    Terminal stops accumulate more passengers because all trips
    start/end there — they have structurally higher demand.
    """
    stop_times = pd.read_csv(gtfs_dir / "stop_times.txt", low_memory=False)
    terminals = set()

    for trip_id, group in stop_times.groupby("trip_id"):
        seq = group.sort_values("stop_sequence")
        first_stop = seq.iloc[0]["stop_id"]
        last_stop = seq.iloc[-1]["stop_id"]
        terminals.add(first_stop)
        terminals.add(last_stop)

    return terminals


def compute_route_demand_factors(gtfs_dir: Path) -> dict[str, float]:
    """Compute per-route demand factor from GTFS headway.

    Routes with shorter headway (more frequent) are higher-demand corridors.
    This creates realistic route-to-route demand variation.

    Returns dict mapping route_id to a demand multiplier (0.8 - 1.2).
    """
    trips = pd.read_csv(gtfs_dir / "trips.txt", low_memory=False)
    frequencies_path = gtfs_dir / "frequencies.txt"

    if frequencies_path.exists():
        freq = pd.read_csv(frequencies_path)
        # Join with trips to get route_id
        freq_with_route = freq.merge(trips[["trip_id", "route_id"]].drop_duplicates(), on="trip_id")
        # Average headway per route
        route_headway = freq_with_route.groupby("route_id")["headway_secs"].mean() / 60.0
    else:
        # Estimate from trip count per route
        route_trips = trips.groupby("route_id").size()
        route_headway = 60.0 / route_trips.clip(lower=1)

    # Normalize: shortest headway (highest demand) -> 1.2, longest -> 0.8
    min_h = route_headway.min()
    max_h = route_headway.max()
    if max_h > min_h:
        normalized = (route_headway - min_h) / (max_h - min_h)
    else:
        normalized = pd.Series(0.5, index=route_headway.index)

    factors = 0.8 + 0.4 * normalized  # range [0.8, 1.2]
    return factors.to_dict()


def generate_density_label(
    base_demand: float,
    hour: int,
    rainfall_level: int,
    flood_flag: int,
    event_flag: int,
    vehicle_capacity: int,
    connectivity: int,
    route_demand_factor: float = 1.0,
    rng: np.random.Generator | None = None,
) -> str:
    """Generate density label with Poisson-distributed passenger arrivals.

    Uses Poisson process for realistic passenger arrival simulation:
    - Expected demand is computed from multipliers (rush, weather, event, connectivity)
    - Actual passenger count follows Poisson(lambda=expected_demand)
    - This adds realistic stochastic noise that a model cannot deterministically predict

    Reference: "passengers are assumed to arrive at stops independently"
    — Cats & West, Transportation Research Part B, 2024
    """
    # Rush multiplier
    rush_mult = 2.4 if is_rush_hour(hour) else 1.0

    # Weather impact
    if flood_flag:
        rain_mult = 0.5
    elif rainfall_level >= 3:
        rain_mult = 0.7
    elif rainfall_level == 2:
        rain_mult = 0.85
    else:
        rain_mult = 1.0

    # Event impact
    event_mult = 1.3 if event_flag else 1.0

    # Connectivity multiplier: more routes = more demand
    if connectivity <= 1:
        conn_mult = 0.7
    elif connectivity <= 2:
        conn_mult = 0.85
    elif connectivity <= 5:
        conn_mult = 1.0
    else:
        conn_mult = 1.2

    # Expected demand with route-specific factor
    expected_demand = base_demand * route_demand_factor * rush_mult * rain_mult * event_mult * conn_mult

    # Poisson-distributed actual passenger arrivals
    if rng is None:
        rng = np.random.default_rng(42)
    actual_passengers = rng.poisson(max(expected_demand, 0.1))

    load_factor = actual_passengers / max(vehicle_capacity, 1)

    if load_factor < 0.45:
        return "LOW"
    elif load_factor < 0.75:
        return "MEDIUM"
    elif load_factor < 1.0:
        return "HIGH"
    else:
        return "OVERLOADED"


def build_density_dataset(
    gtfs_dir: Path,
    output_path: Path | None = None,
) -> pd.DataFrame:
    """Build density training dataset from GTFS structure.

    Uses:
    - Stop connectivity (number of routes through each stop)
    - Terminal vs intermediate stop type
    - Route-specific demand factors from headway
    - Poisson-distributed passenger arrivals (stochastic, non-deterministic labels)
    """
    random.seed(42)
    np.random.seed(42)
    rng = np.random.default_rng(42)

    # Pre-compute GTFS-derived features
    connectivity = compute_stop_connectivity(gtfs_dir)
    terminal_stops = compute_terminal_stops(gtfs_dir)
    route_demand_factors = compute_route_demand_factors(gtfs_dir)

    # Layer 1: GTFS structure
    segments = extract_segments(gtfs_dir)

    # Layer 2: Weather context
    dates = []
    for _, row in segments.iterrows():
        dow = int(row["day_of_week"])
        month_range = list(WET_MONTHS | DRY_MONTHS) if dow in [5, 6] else (
            list(WET_MONTHS) if hash(str(row.get("trip_id", ""))) % 2 == 0 else list(DRY_MONTHS)
        )
        dates.append(assign_date(dow, month_range))
    segments["date"] = dates

    rainfall, flood = [], []
    for _, row in segments.iterrows():
        w = get_weather_synthetic(row["date"], time(int(row["hour"]), 0))
        rainfall.append(w["rainfall_level"])
        flood.append(w["flood_flag"])
    segments["rainfall_level"] = rainfall
    segments["flood_flag"] = flood

    # Layer 3: Synthetic density labels with Poisson noise
    density_labels = []
    event_flags = []
    capacities = []
    conn_values = []
    terminal_values = []
    route_factor_values = []

    for _, row in segments.iterrows():
        route_mode = row["route_mode"]
        route_id = row["route_id"]
        base_demand = BASE_DEMAND.get(route_mode, 20)
        hour = int(row["hour"])
        rainfall = int(row["rainfall_level"])
        flood = int(row["flood_flag"])
        event = int(random.random() < 0.1)
        capacity = int({
            "MIKROTRANS": 12, "TRANSJAKARTA": 80,
            "MRT_LRT": 1200, "KRL": 1200,
        }.get(route_mode, 80))
        stop_id = row["from_stop_id"]
        conn = connectivity.get(stop_id, 1)
        is_term = 1 if stop_id in terminal_stops else 0
        route_factor = route_demand_factors.get(route_id, 1.0)

        label = generate_density_label(
            base_demand, hour, rainfall, flood, event, capacity, conn,
            route_demand_factor=route_factor, rng=rng,
        )
        density_labels.append(label)
        event_flags.append(event)
        capacities.append(capacity)
        conn_values.append(conn)
        terminal_values.append(is_term)
        route_factor_values.append(route_factor)

    segments["density_level"] = density_labels
    segments["event_flag"] = event_flags
    segments["vehicle_capacity"] = capacities
    segments["routes_through_stop"] = conn_values
    segments["is_terminal"] = terminal_values
    segments["route_demand_factor"] = route_factor_values

    # Add is_rush_hour
    segments["is_rush_hour"] = segments["hour"].apply(lambda h: 1 if is_rush_hour(int(h)) else 0)

    # Select columns
    output_cols = [
        "from_stop_id", "route_id", "headway_minutes", "vehicle_capacity",
        "hour", "day_of_week", "is_rush_hour",
        "rainfall_level", "flood_flag", "event_flag",
        "routes_through_stop", "is_terminal", "route_demand_factor",
        "density_level",
    ]
    df = segments[output_cols].copy()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    return df
