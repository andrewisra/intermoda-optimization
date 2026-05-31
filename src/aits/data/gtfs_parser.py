from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.aits.config import PROCESSED_DIR, RAW_DIR, WALKING_CATEGORY_DEFAULTS
from src.aits.data.gtfs_downloader import get_gtfs_path

REQUIRED_FILES = ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
OPTIONAL_FILES = [
    "shapes.txt",
    "calendar.txt",
    "calendar_dates.txt",
    "agency.txt",
    "fare_rules.txt",
    "frequencies.txt",
    "transfers.txt",
]
MODE_MAP = {
    "transjakarta": "TRANSJAKARTA",
    "jakarta-integrated-transit": "TRANSJAKARTA",
    "jak": "TRANSJAKARTA",
    "bus": "TRANSJAKARTA",
    "mrt-jakarta": "MRT",
    "mrt": "MRT",
    "lrt-jakarta": "LRT",
    "lrt": "LRT",
    "krl": "KRL",
    "kai-commuter": "KRL",
    "microtrans": "MIKROTRANS",
}
DEFAULT_WALK_SPEED_KMH = 4.5
MAX_TRANSFER_DISTANCE_M = 800.0


def _normalize_gtfs_time(value: object) -> str:
    if not isinstance(value, str):
        return str(value)
    parts = value.split(":")
    if len(parts) != 3:
        return value
    hours, minutes, seconds = [int(float(p)) for p in parts]
    if hours >= 24:
        hours = hours % 24
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _infer_mode(route_id: str, route_name: str = "", agency_id: str = "") -> str:
    combined = f"{route_id} {route_name} {agency_id}".lower()
    for key, mode in MODE_MAP.items():
        if key in combined:
            return mode
    return "TRANSJAKARTA"


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_m = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _walking_category(minutes: float) -> str:
    for category, cfg in WALKING_CATEGORY_DEFAULTS.items():
        if cfg["min"] <= minutes <= cfg["max"]:
            return category
    return "VERY_LONG"


def _write_processed(df: pd.DataFrame, stem: str) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(PROCESSED_DIR / f"{stem}.parquet", index=False)
    except Exception:
        df.to_csv(PROCESSED_DIR / f"{stem}.csv", index=False)


def parse_gtfs(gtfs_path: str | Path | None = None) -> dict[str, pd.DataFrame]:
    """Parse GTFS into clean processed dataframes.

    This parser is adapted from the teammate GTFS work and moved into the AITS
    architecture, so there is no separate legacy data_pipeline package anymore.
    """
    path = Path(gtfs_path) if gtfs_path else get_gtfs_path()
    missing = [name for name in REQUIRED_FILES if not (path / name).exists()]
    if missing:
        raise FileNotFoundError(f"GTFS incomplete at {path}. Missing files: {missing}")

    frames: dict[str, pd.DataFrame] = {}
    for name in REQUIRED_FILES + OPTIONAL_FILES:
        file_path = path / name
        if file_path.exists():
            frames[name.replace(".txt", "")] = pd.read_csv(file_path, low_memory=False)

    routes = frames.get("routes")
    trips = frames.get("trips")
    stop_times = frames.get("stop_times")
    stops = frames.get("stops")

    route_mode: dict[str, str] = {}
    if routes is not None:
        for _, row in routes.iterrows():
            route_id = str(row.get("route_id", ""))
            route_mode[route_id] = _infer_mode(
                route_id,
                str(row.get("route_long_name", row.get("route_short_name", ""))),
                str(row.get("agency_id", "")),
            )
        routes["mode"] = routes["route_id"].astype(str).map(route_mode).fillna("TRANSJAKARTA")

    if stop_times is not None:
        for col in ["arrival_time", "departure_time"]:
            if col in stop_times.columns:
                stop_times[col] = stop_times[col].apply(_normalize_gtfs_time)
        if "route_id" not in stop_times.columns and trips is not None and "route_id" in trips.columns:
            mapping = trips[["trip_id", "route_id"]].drop_duplicates("trip_id").set_index("trip_id")["route_id"]
            stop_times["route_id"] = stop_times["trip_id"].map(mapping)
        if "mode" not in stop_times.columns and "route_id" in stop_times.columns:
            stop_times["mode"] = stop_times["route_id"].astype(str).map(route_mode).fillna("TRANSJAKARTA")

    if stops is not None and stop_times is not None and "mode" not in stops.columns:
        stop_mode = (
            stop_times[["stop_id", "mode"]]
            .dropna()
            .drop_duplicates("stop_id")
            .set_index("stop_id")["mode"]
        )
        stops["mode"] = stops["stop_id"].map(stop_mode).fillna("TRANSJAKARTA")
        if "lat" not in stops.columns and "stop_lat" in stops.columns:
            stops["lat"] = stops["stop_lat"]
        if "lon" not in stops.columns and "stop_lon" in stops.columns:
            stops["lon"] = stops["stop_lon"]

    for name, df in frames.items():
        _write_processed(df, f"gtfs_{name}")
    if stops is not None:
        _write_processed(stops, "stops_gtfs")
    if routes is not None:
        _write_processed(routes, "routes_gtfs")
    if stop_times is not None:
        _write_processed(stop_times, "stop_times_gtfs")

    return frames


def build_transfer_nodes_from_gtfs(
    gtfs_path: str | Path | None = None,
    max_distance_m: float = MAX_TRANSFER_DISTANCE_M,
    walk_speed_kmh: float = DEFAULT_WALK_SPEED_KMH,
    max_transfers_per_stop: int = 5,
    grid_size_deg: float = 0.01,
) -> pd.DataFrame:
    """Generate candidate walking transfer links from nearby GTFS stops.

    The output uses the final AITS transfer schema and categorized walking time.
    It is meant as an initial candidate list; high-priority transfer nodes should
    still be validated manually or with field data.
    """
    path = Path(gtfs_path) if gtfs_path else get_gtfs_path()
    stops = pd.read_csv(path / "stops.txt", low_memory=False)
    required = {"stop_id", "stop_lat", "stop_lon"}
    if not required.issubset(stops.columns):
        raise ValueError(f"stops.txt must contain columns {required}")

    stop_times = pd.read_csv(path / "stop_times.txt", low_memory=False)
    trips = pd.read_csv(path / "trips.txt", low_memory=False)
    merged = stop_times[["trip_id", "stop_id"]].merge(
        trips[["trip_id", "route_id"]], on="trip_id", how="left"
    )
    stop_routes: dict[str, set[str]] = {}
    for stop_id, group in merged.groupby("stop_id"):
        stop_routes[str(stop_id)] = set(group["route_id"].dropna().astype(str))

    grid: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for _, row in stops.iterrows():
        lat = float(row["stop_lat"])
        lon = float(row["stop_lon"])
        grid[(int(math.floor(lat / grid_size_deg)), int(math.floor(lon / grid_size_deg)))].append(
            {"stop_id": str(row["stop_id"]), "lat": lat, "lon": lon}
        )

    candidates: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for (gx, gy), cell_stops in grid.items():
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                for s1 in cell_stops:
                    for s2 in grid.get((gx + dx, gy + dy), []):
                        if s1["stop_id"] == s2["stop_id"]:
                            continue
                        routes1 = stop_routes.get(s1["stop_id"], set())
                        routes2 = stop_routes.get(s2["stop_id"], set())
                        if not routes1 or not routes2 or routes1 & routes2:
                            continue
                        distance = _haversine_m(s1["lat"], s1["lon"], s2["lat"], s2["lon"])
                        if distance <= max_distance_m:
                            candidates[s1["stop_id"]].append((s2["stop_id"], distance))

    rows = []
    seen: set[tuple[str, str]] = set()
    counter = 1
    for from_stop, nearby in candidates.items():
        for to_stop, distance in sorted(nearby, key=lambda item: item[1])[:max_transfers_per_stop]:
            pair = tuple(sorted([from_stop, to_stop]))
            if pair in seen:
                continue
            seen.add(pair)
            minutes = round(distance / (walk_speed_kmh * 1000 / 60), 1)
            category = _walking_category(minutes)
            rows.append(
                {
                    "transfer_id": f"GTFS_TRF_{counter:05d}",
                    "from_stop_id": from_stop,
                    "to_station_id": to_stop,
                    "walking_category": category,
                    "walking_min_minutes": WALKING_CATEGORY_DEFAULTS[category]["min"],
                    "walking_max_minutes": WALKING_CATEGORY_DEFAULTS[category]["max"],
                    "default_walking_minutes": max(minutes, float(WALKING_CATEGORY_DEFAULTS[category]["default"])),
                    "distance_meters": round(distance, 1),
                    "accessibility_note": "Auto-generated candidate from GTFS proximity; validate before production use.",
                }
            )
            counter += 1

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["from_stop_id", "default_walking_minutes"]).reset_index(drop=True)
    _write_processed(df, "transfer_nodes_gtfs_candidates")
    return df


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse GTFS into AITS processed data")
    parser.add_argument("--gtfs-path", default=None)
    parser.add_argument("--build-transfers", action="store_true")
    args = parser.parse_args()

    frames = parse_gtfs(args.gtfs_path)
    for name, df in frames.items():
        print(f"{name}: {len(df)} rows")
    if args.build_transfers:
        transfers = build_transfer_nodes_from_gtfs(args.gtfs_path)
        print(f"Generated {len(transfers)} candidate transfer links")


if __name__ == "__main__":
    main()
