from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

from src.aits.config import RAW_DIR, PROCESSED_DIR, MODEL_DIR, WALKING_CATEGORY_DEFAULTS, USER_WALKING_PROFILES

RNG = np.random.default_rng(42)


def ensure_dirs() -> None:
    for directory in [RAW_DIR, PROCESSED_DIR, MODEL_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def generate_stops() -> pd.DataFrame:
    rows = [
        ("TJ_DUKUH_ATAS", "Halte Dukuh Atas", "TRANSJAKARTA", -6.2008, 106.8229),
        ("MRT_DUKUH_ATAS", "Stasiun MRT Dukuh Atas", "MRT", -6.2002, 106.8236),
        ("KRL_SUDIRMAN", "Stasiun Sudirman", "KRL", -6.2017, 106.8211),
        ("TJ_HARMONI", "Halte Harmoni", "TRANSJAKARTA", -6.1664, 106.8200),
        ("TJ_BLOK_M", "Terminal Blok M", "TRANSJAKARTA", -6.2445, 106.8008),
        ("MRT_BLOK_M", "Stasiun MRT Blok M", "MRT", -6.2440, 106.7989),
        ("TJ_LEBAK_BULUS", "Halte Lebak Bulus", "TRANSJAKARTA", -6.2890, 106.7741),
        ("MRT_LEBAK_BULUS", "Stasiun MRT Lebak Bulus", "MRT", -6.2892, 106.7743),
        ("TJ_CAWANG", "Halte Cawang", "TRANSJAKARTA", -6.2433, 106.8688),
        ("KRL_CAWANG", "Stasiun Cawang", "KRL", -6.2423, 106.8589),
        ("TJ_TANAH_ABANG", "Halte Tanah Abang", "TRANSJAKARTA", -6.1862, 106.8100),
        ("KRL_TANAH_ABANG", "Stasiun Tanah Abang", "KRL", -6.1856, 106.8108),
    ]
    return pd.DataFrame(rows, columns=["stop_id", "stop_name", "mode", "lat", "lon"])


def generate_routes() -> pd.DataFrame:
    rows = [
        ("TJ_01", "Blok M - Kota via Dukuh Atas", "TRANSJAKARTA", 8, 80),
        ("TJ_02", "Harmoni - Dukuh Atas", "TRANSJAKARTA", 10, 80),
        ("MRT_NS", "MRT North-South", "MRT", 5, 1200),
        ("KRL_CL", "KRL Commuter Line", "KRL", 10, 1800),
        ("MKT_01", "Mikrotrans Feeder Cawang", "MIKROTRANS", 12, 12),
    ]
    return pd.DataFrame(rows, columns=["route_id", "route_name", "mode", "scheduled_headway_minutes", "default_capacity"])


def generate_transfer_nodes() -> pd.DataFrame:
    rows = [
        ("TRF001", "TJ_DUKUH_ATAS", "MRT_DUKUH_ATAS", "VERY_SHORT", "Normal pedestrian corridor"),
        ("TRF002", "KRL_SUDIRMAN", "MRT_DUKUH_ATAS", "SHORT", "Connected urban walking corridor"),
        ("TRF003", "TJ_BLOK_M", "MRT_BLOK_M", "VERY_SHORT", "Close station access"),
        ("TRF004", "TJ_LEBAK_BULUS", "MRT_LEBAK_BULUS", "VERY_SHORT", "Integrated terminal access"),
        ("TRF005", "TJ_CAWANG", "KRL_CAWANG", "MEDIUM", "Longer walking segment, road crossing"),
        ("TRF006", "TJ_TANAH_ABANG", "KRL_TANAH_ABANG", "SHORT", "Crowded area near market/station"),
    ]
    df = pd.DataFrame(rows, columns=["transfer_id", "from_stop_id", "to_station_id", "walking_category", "accessibility_note"])
    df["walking_min_minutes"] = df["walking_category"].map(lambda x: WALKING_CATEGORY_DEFAULTS[x]["min"])
    df["walking_max_minutes"] = df["walking_category"].map(lambda x: WALKING_CATEGORY_DEFAULTS[x]["max"])
    df["default_walking_minutes"] = df["walking_category"].map(lambda x: WALKING_CATEGORY_DEFAULTS[x]["default"])
    return df


def generate_user_profiles() -> pd.DataFrame:
    rows = [
        ("U_FAST", "FAST", USER_WALKING_PROFILES["FAST"], True),
        ("U_STANDARD", "STANDARD", USER_WALKING_PROFILES["STANDARD"], True),
        ("U_RELAXED", "RELAXED", USER_WALKING_PROFILES["RELAXED"], True),
        ("U_ASSISTED", "ASSISTED", USER_WALKING_PROFILES["ASSISTED"], True),
        ("U_ANON", "STANDARD", USER_WALKING_PROFILES["STANDARD"], False),
    ]
    return pd.DataFrame(rows, columns=["user_id", "walking_profile", "walking_multiplier", "consent_personalization"])


def generate_rail_schedule() -> pd.DataFrame:
    date = datetime(2026, 5, 23, 6, 0)
    rows = []
    stations = [
        ("MRT_DUKUH_ATAS", "MRT_NS", "MRT", 5),
        ("MRT_BLOK_M", "MRT_NS", "MRT", 5),
        ("MRT_LEBAK_BULUS", "MRT_NS", "MRT", 5),
        ("KRL_CAWANG", "KRL_CL", "KRL", 10),
        ("KRL_TANAH_ABANG", "KRL_CL", "KRL", 10),
    ]
    for station_id, route_id, mode, headway in stations:
        current = date
        idx = 1
        while current <= datetime(2026, 5, 23, 10, 0):
            rows.append((f"{route_id}_{station_id}_{idx:03d}", route_id, mode, station_id, current.isoformat()))
            current += timedelta(minutes=headway)
            idx += 1
    return pd.DataFrame(rows, columns=["trip_id", "route_id", "mode", "station_id", "departure_time"])


def generate_non_rail_schedule() -> pd.DataFrame:
    rows = []
    route_stops = [
        ("TJ_01", "TRANSJAKARTA", "TJ_DUKUH_ATAS", 8, 80),
        ("TJ_02", "TRANSJAKARTA", "TJ_DUKUH_ATAS", 10, 80),
        ("TJ_01", "TRANSJAKARTA", "TJ_BLOK_M", 8, 80),
        ("TJ_01", "TRANSJAKARTA", "TJ_LEBAK_BULUS", 8, 80),
        ("MKT_01", "MIKROTRANS", "TJ_CAWANG", 12, 12),
        ("TJ_02", "TRANSJAKARTA", "TJ_TANAH_ABANG", 10, 80),
    ]
    base = datetime(2026, 5, 23, 6, 0)
    for route_id, mode, stop_id, headway, capacity in route_stops:
        current = base + timedelta(minutes=int(RNG.integers(0, headway)))
        idx = 1
        while current <= datetime(2026, 5, 23, 10, 0):
            delay = max(0, RNG.normal(2.0 if 7 <= current.hour <= 8 else 0.8, 2.0))
            rows.append((f"{route_id}_{stop_id}_{idx:03d}", route_id, mode, stop_id, current.isoformat(), capacity, round(float(delay), 2)))
            current += timedelta(minutes=headway)
            idx += 1
    return pd.DataFrame(rows, columns=["trip_id", "route_id", "mode", "stop_id", "scheduled_arrival", "vehicle_capacity", "historical_delay_minutes"])


def generate_training_eta(n: int = 4000) -> pd.DataFrame:
    rows = []
    route_ids = ["TJ_01", "TJ_02", "MKT_01"]
    stop_ids = ["TJ_DUKUH_ATAS", "TJ_BLOK_M", "TJ_LEBAK_BULUS", "TJ_CAWANG", "TJ_TANAH_ABANG"]
    for _ in range(n):
        route_id = RNG.choice(route_ids)
        stop_id = RNG.choice(stop_ids)
        hour = int(RNG.integers(5, 23))
        day_of_week = int(RNG.integers(0, 7))
        traffic_level = int(np.clip(RNG.normal(3 if 7 <= hour <= 9 or 16 <= hour <= 19 else 2, 1), 0, 5))
        rainfall_level = int(RNG.choice([0, 0, 0, 1, 1, 2, 3]))
        incident_flag = int(RNG.choice([0, 0, 0, 0, 1]))
        passenger_density_score = float(np.clip(RNG.beta(2, 4) + (0.2 if 7 <= hour <= 9 else 0), 0, 1))
        scheduled_travel_minutes = float(RNG.integers(6, 25))
        mode_micro = 1 if route_id == "MKT_01" else 0
        noise = RNG.normal(0, 1.2)
        delay = (
            0.6 * traffic_level
            + 0.7 * rainfall_level
            + 3.5 * incident_flag
            + 2.0 * passenger_density_score
            + 1.3 * mode_micro
            + (2.0 if 7 <= hour <= 9 or 16 <= hour <= 19 else 0.2)
            + noise
        )
        delay = max(0, delay)
        rows.append((route_id, stop_id, hour, day_of_week, traffic_level, rainfall_level, incident_flag, passenger_density_score, scheduled_travel_minutes, round(float(delay), 3)))
    return pd.DataFrame(rows, columns=["route_id", "stop_id", "hour", "day_of_week", "traffic_level", "rainfall_level", "incident_flag", "passenger_density_score", "scheduled_travel_minutes", "delay_minutes"])


def density_label(load_factor: float) -> str:
    if load_factor < 0.45:
        return "LOW"
    if load_factor < 0.75:
        return "MEDIUM"
    if load_factor < 1.0:
        return "HIGH"
    return "OVERLOADED"


def generate_training_density(n: int = 4000) -> pd.DataFrame:
    rows = []
    route_ids = ["TJ_01", "TJ_02", "MKT_01", "MRT_NS", "KRL_CL"]
    stop_ids = ["TJ_DUKUH_ATAS", "MRT_DUKUH_ATAS", "TJ_BLOK_M", "TJ_CAWANG", "KRL_CAWANG", "KRL_TANAH_ABANG"]
    for _ in range(n):
        route_id = RNG.choice(route_ids)
        stop_id = RNG.choice(stop_ids)
        hour = int(RNG.integers(5, 23))
        day_of_week = int(RNG.integers(0, 7))
        capacity = int(12 if route_id == "MKT_01" else (80 if route_id.startswith("TJ") else 1200))
        headway = int(12 if route_id == "MKT_01" else (8 if route_id.startswith("TJ") else 5))
        rush_multiplier = 2.4 if 7 <= hour <= 9 or 16 <= hour <= 19 else 1.0
        rain = int(RNG.choice([0, 0, 1, 2, 3]))
        event_flag = int(RNG.choice([0, 0, 0, 1]))
        base = capacity * (0.25 + 0.5 * RNG.random())
        tap_in_count_15m = int(max(0, RNG.normal(base * rush_multiplier * (1 + 0.25 * event_flag), capacity * 0.15)))
        load_factor = tap_in_count_15m / max(capacity, 1)
        label = density_label(load_factor)
        rows.append((stop_id, route_id, hour, day_of_week, tap_in_count_15m, headway, capacity, event_flag, rain, label, round(float(load_factor), 3)))
    return pd.DataFrame(rows, columns=["stop_id", "route_id", "hour", "day_of_week", "tap_in_count_15m", "scheduled_headway_minutes", "vehicle_capacity", "event_flag", "rainfall_level", "density_level", "load_factor"])


def generate_incidents() -> pd.DataFrame:
    rows = [
        ("INC001", "2026-05-23T07:20:00", "TJ_DUKUH_ATAS", "TRAFFIC", 2, "Congestion near business district", True),
        ("INC002", "2026-05-23T08:15:00", "TJ_CAWANG", "ACCIDENT", 4, "Road accident affects feeder corridor", True),
    ]
    return pd.DataFrame(rows, columns=["incident_id", "timestamp", "location_stop_id", "incident_type", "severity", "description", "is_active"])


def write_csv(df: pd.DataFrame, name: str) -> None:
    df.to_csv(RAW_DIR / name, index=False)


def generate_all() -> None:
    ensure_dirs()
    write_csv(generate_stops(), "stops.csv")
    write_csv(generate_routes(), "routes.csv")
    write_csv(generate_transfer_nodes(), "transfer_nodes.csv")
    write_csv(generate_user_profiles(), "user_profiles.csv")
    write_csv(generate_rail_schedule(), "rail_schedule.csv")
    write_csv(generate_non_rail_schedule(), "non_rail_schedule.csv")
    write_csv(generate_training_eta(), "training_eta.csv")
    write_csv(generate_training_density(), "training_density.csv")
    write_csv(generate_incidents(), "incidents.csv")
    print(f"Demo data generated in {RAW_DIR}")


if __name__ == "__main__":
    generate_all()
