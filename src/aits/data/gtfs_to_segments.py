"""Extract stop-to-stop segment skeleton from Transjakarta GTFS data.

Each segment represents one bus traveling between two consecutive stops,
with scheduled times, headway, and route metadata.
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path
from datetime import time, datetime


DEFAULT_HEADWAY_MINUTES = 6


def compute_scheduled_travel_seconds(departure: time, arrival: time) -> int:
    """Compute travel time in seconds between two times."""
    dep_dt = datetime(2024, 1, 1, departure.hour, departure.minute, departure.second)
    arr_dt = datetime(2024, 1, 1, arrival.hour, arrival.minute, arrival.second)
    delta = (arr_dt - dep_dt).total_seconds()
    return max(0, int(delta))


def _parse_gtfs_time(value: str) -> time:
    """Parse GTFS time string (HH:MM:SS, may have hours >= 24)."""
    parts = str(value).split(":")
    if len(parts) != 3:
        return time(0, 0)
    hours, minutes, seconds = [int(float(p)) for p in parts]
    if hours >= 24:
        hours = hours % 24
    return time(hours, minutes, seconds)


def get_headway_for_time(
    frequencies: pd.DataFrame,
    trip_id: str,
    query_time: time,
) -> float:
    """Look up headway in seconds for a trip at a given time."""
    trip_freqs = frequencies[frequencies["trip_id"] == trip_id]
    if trip_freqs.empty:
        return DEFAULT_HEADWAY_MINUTES * 60

    for _, row in trip_freqs.iterrows():
        start = _parse_gtfs_time(row["start_time"])
        end = _parse_gtfs_time(row["end_time"])
        if start <= query_time <= end:
            return float(row["headway_secs"])

    return DEFAULT_HEADWAY_MINUTES * 60


def build_segment_row(
    trip_id: str,
    route_id: str,
    direction: int,
    from_stop_id: str,
    to_stop_id: str,
    stop_sequence: int,
    scheduled_departure: time,
    scheduled_arrival: time,
    headway_minutes: float,
    route_mode: str,
) -> dict:
    """Build a single segment row dict."""
    travel_sec = compute_scheduled_travel_seconds(scheduled_departure, scheduled_arrival)
    return {
        "trip_id": trip_id,
        "route_id": route_id,
        "direction": direction,
        "from_stop_id": from_stop_id,
        "to_stop_id": to_stop_id,
        "stop_sequence": stop_sequence,
        "scheduled_departure": scheduled_departure.strftime("%H:%M:%S"),
        "scheduled_arrival": scheduled_arrival.strftime("%H:%M:%S"),
        "scheduled_travel_seconds": travel_sec,
        "hour": scheduled_departure.hour,
        "day_of_week": 0,  # will be set by caller
        "headway_minutes": round(headway_minutes / 60, 1),
        "route_mode": route_mode,
    }


def _load_mode_map(gtfs_dir: Path) -> dict[str, str]:
    """Build route_id -> mode mapping from routes.txt."""
    routes_path = gtfs_dir / "routes.txt"
    if not routes_path.exists():
        return {}
    routes = pd.read_csv(routes_path, low_memory=False)
    mode_map = {}
    for _, row in routes.iterrows():
        rid = str(row.get("route_id", ""))
        rname = str(row.get("route_long_name", row.get("route_short_name", ""))).lower()
        aid = str(row.get("agency_id", "")).lower()
        # Only classify as rail if agency is mrt/lrt/krl (not bus routes that merely mention station names)
        if any(k in aid for k in ["mrt", "lrt"]):
            mode_map[rid] = "MRT_LRT"
        elif any(k in aid for k in ["krl", "kai", "commuter"]):
            mode_map[rid] = "KRL"
        elif any(k in aid for k in ["micro", "feeder", "mkt"]):
            mode_map[rid] = "MIKROTRANS"
        else:
            mode_map[rid] = "TRANSJAKARTA"
    return mode_map


def _load_service_days(gtfs_dir: Path) -> dict[str, int]:
    """Build service_id -> day_of_week mapping from calendar.txt."""
    cal_path = gtfs_dir / "calendar.txt"
    if not cal_path.exists():
        return {}
    cal = pd.read_csv(cal_path, low_memory=False)
    day_map = {}
    for _, row in cal.iterrows():
        sid = str(row.get("service_id", ""))
        if row.get("monday", 0) == 1:
            day_map[sid] = 0
        elif row.get("tuesday", 0) == 1:
            day_map[sid] = 1
        elif row.get("wednesday", 0) == 1:
            day_map[sid] = 2
        elif row.get("thursday", 0) == 1:
            day_map[sid] = 3
        elif row.get("friday", 0) == 1:
            day_map[sid] = 4
        elif row.get("saturday", 0) == 1:
            day_map[sid] = 5
        elif row.get("sunday", 0) == 1:
            day_map[sid] = 6
        else:
            day_map[sid] = 0
    return day_map


def extract_segments(gtfs_dir: Path) -> pd.DataFrame:
    """Extract stop-to-stop segments from GTFS data.

    Returns a DataFrame with one row per segment (consecutive stop pair per trip).
    """
    stop_times = pd.read_csv(gtfs_dir / "stop_times.txt", low_memory=False)
    trips = pd.read_csv(gtfs_dir / "trips.txt", low_memory=False)

    # Load supporting data
    freq_path = gtfs_dir / "frequencies.txt"
    frequencies = pd.read_csv(freq_path, low_memory=False) if freq_path.exists() else pd.DataFrame()
    mode_map = _load_mode_map(gtfs_dir)
    service_days = _load_service_days(gtfs_dir)

    # Join trips for route_id, direction, service_id
    trip_meta = trips[["trip_id", "route_id", "direction_id", "service_id"]].drop_duplicates("trip_id")
    trip_meta = trip_meta.set_index("trip_id")

    stop_times = stop_times.sort_values(["trip_id", "stop_sequence"])

    rows = []
    for trip_id, group in stop_times.groupby("trip_id"):
        if trip_id not in trip_meta.index:
            continue
        meta = trip_meta.loc[trip_id]
        route_id = str(meta["route_id"])
        direction = int(meta.get("direction_id", 0))
        service_id = str(meta.get("service_id", ""))
        day_of_week = service_days.get(service_id, 0)
        route_mode = mode_map.get(route_id, "TRANSJAKARTA")

        stops = group.sort_values("stop_sequence").reset_index(drop=True)

        for i in range(len(stops) - 1):
            row_dep = stops.iloc[i]
            row_arr = stops.iloc[i + 1]

            dep_time = _parse_gtfs_time(row_dep["departure_time"])
            arr_time = _parse_gtfs_time(row_arr["arrival_time"])

            headway_secs = get_headway_for_time(frequencies, trip_id, dep_time)

            seg = build_segment_row(
                trip_id=trip_id,
                route_id=route_id,
                direction=direction,
                from_stop_id=str(row_dep["stop_id"]),
                to_stop_id=str(row_arr["stop_id"]),
                stop_sequence=int(row_dep["stop_sequence"]),
                scheduled_departure=dep_time,
                scheduled_arrival=arr_time,
                headway_minutes=headway_secs,
                route_mode=route_mode,
            )
            seg["day_of_week"] = day_of_week
            rows.append(seg)

    return pd.DataFrame(rows)
