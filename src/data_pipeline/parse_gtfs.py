from __future__ import annotations

import math
import zipfile
from pathlib import Path

import pandas as pd

from src.config import RAW_DIR, PROCESSED_DIR
from src.utils import save_table

REQUIRED_FILES = ["stops.txt", "routes.txt", "trips.txt", "stop_times.txt"]
OPTIONAL_FILES = ["shapes.txt", "calendar.txt", "calendar_dates.txt", "agency.txt", "fare_rules.txt", "transfers.txt"]
MODE_MAP = {
    "transjakarta": "Transjakarta",
    "jakarta-integrated-transit": "Transjakarta",
    "mrt-jakarta": "MRT",
    "lrt-jakarta": "LRT",
    "krl": "KRL",
    "kai-commuter": "KRL",
    "microtrans": "Mikrotrans",
}
DEFAULT_TRANSFER_WALK_SPEED_KMH = 4.5
MAX_TRANSFER_DISTANCE_M = 800


def _gtfs_dir() -> Path:
    candidates = [RAW_DIR / "gtfs_transjakarta", RAW_DIR / "gtfs"]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    zip_candidates = list(RAW_DIR.glob("*.zip"))
    if zip_candidates:
        out = RAW_DIR / "gtfs_transjakarta"
        out.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_candidates[0], "r") as zf:
            zf.extractall(out)
        return out
    raise FileNotFoundError("Letakkan file GTFS .zip atau folder gtfs_transjakarta di data/raw")


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in meters between two lat/lon points."""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _infer_mode(route_id: str, route_name: str, agency_id: str = "") -> str:
    """Infer transit mode from GTFS route attributes."""
    combined = f"{route_id} {route_name} {agency_id}".lower()
    for keyword, mode in MODE_MAP.items():
        if keyword in combined:
            return mode
    if "bus" in combined or "corridor" in combined or "jak" in combined:
        return "Transjakarta"
    return "Transjakarta"


def _normalize_gtfs_time(time_str: str) -> str:
    """Normalize GTFS time strings that can exceed 24:00:00."""
    if not isinstance(time_str, str):
        return str(time_str)
    parts = time_str.split(":")
    if len(parts) != 3:
        return time_str
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    if hours >= 24:
        hours -= 24
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_gtfs(gtfs_path: Path | None = None) -> dict[str, pd.DataFrame]:
    """Parse GTFS files into DataFrames and save to processed directory.

    Returns dict mapping file name (without .txt) to DataFrame.
    """
    gtfs_path = Path(gtfs_path) if gtfs_path else _gtfs_dir()
    missing = [f for f in REQUIRED_FILES if not (gtfs_path / f).exists()]
    if missing:
        raise FileNotFoundError(f"GTFS tidak lengkap. File hilang: {missing}")

    frames: dict[str, pd.DataFrame] = {}

    for name in REQUIRED_FILES + OPTIONAL_FILES:
        fpath = gtfs_path / name
        if fpath.exists():
            df = pd.read_csv(fpath)
            key = name.replace(".txt", "")
            frames[key] = df

    stops_df = frames.get("stops")
    routes_df = frames.get("routes")
    trips_df = frames.get("trips")
    stop_times_df = frames.get("stop_times")

    if stops_df is not None and routes_df is not None:
        mode_lookup: dict[str, str] = {}
        for _, r in routes_df.iterrows():
            mode_lookup[r["route_id"]] = _infer_mode(
                str(r.get("route_id", "")),
                str(r.get("route_long_name", r.get("route_short_name", ""))),
                str(r.get("agency_id", "")),
            )
        if "mode" not in stops_df.columns and stop_times_df is not None:
            if "route_id" in stop_times_df.columns and "stop_id" in stop_times_df.columns:
                stop_route_mode: dict[str, str] = {}
                for _, row in stop_times_df[["stop_id", "route_id"]].drop_duplicates().iterrows():
                    rid = row["route_id"]
                    if rid in mode_lookup:
                        stop_route_mode[row["stop_id"]] = mode_lookup[rid]
                stops_df["mode"] = stops_df["stop_id"].map(stop_route_mode).fillna("Transjakarta")

    if stop_times_df is not None:
        for col in ["arrival_time", "departure_time"]:
            if col in stop_times_df.columns:
                stop_times_df[col] = stop_times_df[col].apply(_normalize_gtfs_time)

    if stop_times_df is not None and trips_df is not None and "route_id" not in stop_times_df.columns:
        if "route_id" in trips_df.columns:
            trip_route = trips_df[["trip_id", "route_id"]].drop_duplicates("trip_id").set_index("trip_id")
            stop_times_df["route_id"] = stop_times_df["trip_id"].map(trip_route["route_id"])

    if stop_times_df is not None and "mode" not in stop_times_df.columns and "route_id" in stop_times_df.columns:
        stop_times_df["mode"] = stop_times_df["route_id"].map(mode_lookup).fillna("Transjakarta")

    for key, df in frames.items():
        try:
            save_table(df, PROCESSED_DIR / f"gtfs_{key}.parquet")
        except Exception:
            df.to_csv(PROCESSED_DIR / f"gtfs_{key}.csv", index=False)

    if stops_df is not None:
        try:
            save_table(stops_df, PROCESSED_DIR / "stops.parquet")
        except Exception:
            stops_df.to_csv(PROCESSED_DIR / "stops.csv", index=False)

    if stop_times_df is not None:
        try:
            save_table(stop_times_df, PROCESSED_DIR / "stop_times.parquet")
        except Exception:
            stop_times_df.to_csv(PROCESSED_DIR / "stop_times.csv", index=False)

    if routes_df is not None:
        try:
            save_table(routes_df, PROCESSED_DIR / "routes.parquet")
        except Exception:
            routes_df.to_csv(PROCESSED_DIR / "routes.csv", index=False)

    return frames


def build_transfer_nodes_from_gtfs(
    gtfs_path: Path | None = None,
    max_distance_m: float = MAX_TRANSFER_DISTANCE_M,
    walk_speed_kmh: float = DEFAULT_TRANSFER_WALK_SPEED_KMH,
    max_transfers_per_stop: int = 5,
    grid_size_deg: float = 0.01,
) -> pd.DataFrame:
    """Auto-generate transfer nodes by finding GTFS stops within walking distance.

    Uses spatial grid for O(n) performance instead of O(n^2).
    Only pairs stops that belong to different routes (intermodal transfers).
    Limits output to max_transfers_per_stop nearest neighbors per stop.
    """
    gtfs_path = Path(gtfs_path) if gtfs_path else _gtfs_dir()
    stops_path = gtfs_path / "stops.txt"
    if not stops_path.exists():
        raise FileNotFoundError(f"stops.txt not found in {gtfs_path}")

    stops = pd.read_csv(stops_path)
    required_cols = {"stop_id", "stop_lat", "stop_lon"}
    if not required_cols.issubset(stops.columns):
        raise ValueError(f"stops.txt must contain columns {required_cols}")

    trips_path = gtfs_path / "trips.txt"
    stop_route: dict[str, set[str]] = {}
    if trips_path.exists():
        trips = pd.read_csv(trips_path)
        stop_times = pd.read_csv(gtfs_path / "stop_times.txt")
        merged = stop_times[["trip_id", "stop_id"]].merge(
            trips[["trip_id", "route_id"]], on="trip_id", how="left"
        )
        for stop_id, group in merged.groupby("stop_id"):
            stop_route[str(stop_id)] = set(group["route_id"].dropna().astype(str))
    else:
        for _, row in stops.iterrows():
            stop_route[str(row["stop_id"])] = set()

    from collections import defaultdict

    grid: dict[tuple[int, int], list[dict]] = defaultdict(list)
    for _, row in stops.iterrows():
        lat = float(row["stop_lat"])
        lon = float(row["stop_lon"])
        gx = int(math.floor(lat / grid_size_deg))
        gy = int(math.floor(lon / grid_size_deg))
        grid[(gx, gy)].append({"stop_id": str(row["stop_id"]), "lat": lat, "lon": lon})

    seen_pairs: set[tuple[str, str]] = set()
    candidates: dict[str, list[tuple[str, float]]] = defaultdict(list)

    for (gx, gy), cell_stops in grid.items():
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                neighbor_stops = grid.get((gx + dx, gy + dy), [])
                if not neighbor_stops:
                    continue
                for s1 in cell_stops:
                    for s2 in neighbor_stops:
                        if s1["stop_id"] == s2["stop_id"]:
                            continue
                        dist = _haversine(s1["lat"], s1["lon"], s2["lat"], s2["lon"])
                        if dist > max_distance_m:
                            continue
                        routes1 = stop_route.get(s1["stop_id"], set())
                        routes2 = stop_route.get(s2["stop_id"], set())
                        if not routes1 or not routes2:
                            continue
                        if routes1 & routes2:
                            continue
                        overlap_ratio = len(routes1 & routes2) / min(len(routes1), len(routes2)) if routes1 and routes2 else 1.0
                        if overlap_ratio > 0.3:
                            continue
                        candidates[s1["stop_id"]].append((s2["stop_id"], dist))

    rows = []
    for sid1, nearby in candidates.items():
        nearby_sorted = sorted(nearby, key=lambda x: x[1])[:max_transfers_per_stop]
        for sid2, dist in nearby_sorted:
            pair = tuple(sorted([sid1, sid2]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            walking_minutes = round(dist / (walk_speed_kmh * 1000 / 60), 1)
            category = "short" if walking_minutes <= 4 else ("medium" if walking_minutes <= 8 else "long")
            rows.append({
                "from_stop_id": sid1,
                "to_stop_id": sid2,
                "walking_time_minutes": walking_minutes,
                "distance_meters": round(dist, 1),
                "category": category,
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["from_stop_id", "walking_time_minutes"]).reset_index(drop=True)
    return df


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Parse GTFS data into processed parquet files")
    parser.add_argument("--gtfs-path", type=str, default=None, help="Path to GTFS directory")
    parser.add_argument("--build-transfers", action="store_true", help="Auto-generate transfer nodes from GTFS proximity")
    args = parser.parse_args()

    gtfs_path = Path(args.gtfs_path) if args.gtfs_path else None
    frames = parse_gtfs(gtfs_path)
    print("Parsed GTFS files:")
    for k, v in frames.items():
        print(f"  {k}: {len(v)} rows")

    if args.build_transfers:
        transfers = build_transfer_nodes_from_gtfs(gtfs_path)
        print(f"Generated {len(transfers)} transfer nodes from GTFS proximity")
        try:
            save_table(transfers, PROCESSED_DIR / "transfer_nodes.parquet")
        except Exception:
            transfers.to_csv(PROCESSED_DIR / "transfer_nodes.csv", index=False)


if __name__ == "__main__":
    main()
