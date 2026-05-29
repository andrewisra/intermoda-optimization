from __future__ import annotations

from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from src.config import RAW_DIR, PROCESSED_DIR
from src.utils import save_table

BASE_DATE = datetime(2026, 5, 23, 6, 0, 0)


def make_stops() -> pd.DataFrame:
    """Generate stops across all 6 priority transit hubs in Jakarta."""
    rows = [
        # Dukuh Atas hub (intermodal: TJ + MRT + KRL)
        {"stop_id": "TJ_DUKUH_ATAS", "stop_name": "Halte Dukuh Atas", "mode": "Transjakarta", "lat": -6.2008, "lon": 106.8228, "hub": "Dukuh Atas"},
        {"stop_id": "MRT_DUKUH_ATAS", "stop_name": "Stasiun MRT Dukuh Atas BNI", "mode": "MRT", "lat": -6.2001, "lon": 106.8231, "hub": "Dukuh Atas"},
        {"stop_id": "KRL_SUDIRMAN", "stop_name": "Stasiun KRL Sudirman", "mode": "KRL", "lat": -6.2027, "lon": 106.8235, "hub": "Dukuh Atas"},
        # Blok M hub (TJ + MRT)
        {"stop_id": "TJ_BLOK_M", "stop_name": "Halte Blok M", "mode": "Transjakarta", "lat": -6.2447, "lon": 106.8001, "hub": "Blok M"},
        {"stop_id": "MRT_BLOK_M", "stop_name": "Stasiun MRT Blok M", "mode": "MRT", "lat": -6.2440, "lon": 106.7989, "hub": "Blok M"},
        # Bundaran HI hub (TJ + MRT)
        {"stop_id": "TJ_BUNDARAN_HI", "stop_name": "Halte Bundaran HI", "mode": "Transjakarta", "lat": -6.1938, "lon": 106.8227, "hub": "Bundaran HI"},
        {"stop_id": "MRT_BUNDARAN_HI", "stop_name": "Stasiun MRT Bundaran HI", "mode": "MRT", "lat": -6.1939, "lon": 106.8232, "hub": "Bundaran HI"},
        # Tanah Abang hub (TJ + KRL)
        {"stop_id": "TJ_TANAH_ABANG", "stop_name": "Halte Tanah Abang", "mode": "Transjakarta", "lat": -6.1892, "lon": 106.8135, "hub": "Tanah Abang"},
        {"stop_id": "KRL_TANAH_ABANG", "stop_name": "Stasiun KRL Tanah Abang", "mode": "KRL", "lat": -6.1897, "lon": 106.8142, "hub": "Tanah Abang"},
        # Manggarai hub (TJ + KRL)
        {"stop_id": "TJ_MANGGARAI", "stop_name": "Halte Manggarai", "mode": "Transjakarta", "lat": -6.2171, "lon": 106.8520, "hub": "Manggarai"},
        {"stop_id": "KRL_MANGGARAI", "stop_name": "Stasiun KRL Manggarai", "mode": "KRL", "lat": -6.2165, "lon": 106.8515, "hub": "Manggarai"},
        # Harmoni hub (TJ major BRT)
        {"stop_id": "TJ_HARMONI", "stop_name": "Halte Harmoni", "mode": "Transjakarta", "lat": -6.1744, "lon": 106.8258, "hub": "Harmoni"},
        {"stop_id": "TJ_HARMONI_CENTRAL", "stop_name": "Halte Harmoni Sentral", "mode": "Transjakarta", "lat": -6.1748, "lon": 106.8261, "hub": "Harmoni"},
        # Lebak Bulus hub (TJ + MRT terminus)
        {"stop_id": "TJ_LEBAK_BULUS", "stop_name": "Halte Lebak Bulus", "mode": "Transjakarta", "lat": -6.2865, "lon": 106.7913, "hub": "Lebak Bulus"},
        {"stop_id": "MRT_LEBAK_BULUS", "stop_name": "Stasiun MRT Lebak Bulus Grab", "mode": "MRT", "lat": -6.2898, "lon": 106.7881, "hub": "Lebak Bulus"},
        # Cawang hub (TJ + KRL)
        {"stop_id": "TJ_CAWANG", "stop_name": "Halte Cawang", "mode": "Transjakarta", "lat": -6.2482, "lon": 106.8728, "hub": "Cawang"},
        {"stop_id": "KRL_CAWANG", "stop_name": "Stasiun KRL Cawang", "mode": "KRL", "lat": -6.2429, "lon": 106.8589, "hub": "Cawang"},
        # Velodrome hub (LRT)
        {"stop_id": "LRT_VELODROME", "stop_name": "Stasiun LRT Velodrome", "mode": "LRT", "lat": -6.1840, "lon": 106.8790, "hub": "Velodrome"},
        # Kampung Bandan hub (TJ + KRL)
        {"stop_id": "TJ_KAMPUNG_BANDAN", "stop_name": "Halte Kampung Bandan", "mode": "Transjakarta", "lat": -6.1552, "lon": 106.8326, "hub": "Kampung Bandan"},
        {"stop_id": "KRL_KAMPUNG_BANDAN", "stop_name": "Stasiun KRL Kampung Bandan", "mode": "KRL", "lat": -6.1548, "lon": 106.8320, "hub": "Kampung Bandan"},
        # Senayan (TJ + MRT corridor)
        {"stop_id": "TJ_SENAYAN", "stop_name": "Halte Senayan", "mode": "Transjakarta", "lat": -6.2274, "lon": 106.8017, "hub": "Senayan"},
        {"stop_id": "MRT_SENAYAN", "stop_name": "Stasiun MRT Istora Mandiri", "mode": "MRT", "lat": -6.2264, "lon": 106.8023, "hub": "Senayan"},
        # Microtrans feeders
        {"stop_id": "MT_DUKUH_ATAS", "stop_name": "Mikrotrans Dukuh Atas", "mode": "Mikrotrans", "lat": -6.2012, "lon": 106.8218, "hub": "Dukuh Atas"},
        {"stop_id": "MT_BLOK_M", "stop_name": "Mikrotrans Blok M", "mode": "Mikrotrans", "lat": -6.2442, "lon": 106.8005, "hub": "Blok M"},
        {"stop_id": "MT_HARMONI", "stop_name": "Mikrotrans Harmoni", "mode": "Mikrotrans", "lat": -6.1746, "lon": 106.8252, "hub": "Harmoni"},
    ]
    return pd.DataFrame(rows)


def make_transfer_nodes() -> pd.DataFrame:
    """Generate intermodal transfer links across all priority hubs."""
    rows = [
        # Dukuh Atas transfers
        {"from_stop_id": "TJ_DUKUH_ATAS", "to_stop_id": "MRT_DUKUH_ATAS", "walking_time_minutes": 6, "category": "short", "distance_meters": 450},
        {"from_stop_id": "TJ_DUKUH_ATAS", "to_stop_id": "KRL_SUDIRMAN", "walking_time_minutes": 8, "category": "medium", "distance_meters": 600},
        {"from_stop_id": "TJ_DUKUH_ATAS", "to_stop_id": "MT_DUKUH_ATAS", "walking_time_minutes": 2, "category": "short", "distance_meters": 150},
        {"from_stop_id": "MRT_DUKUH_ATAS", "to_stop_id": "KRL_SUDIRMAN", "walking_time_minutes": 4, "category": "short", "distance_meters": 300},
        # Blok M transfers
        {"from_stop_id": "TJ_BLOK_M", "to_stop_id": "MRT_BLOK_M", "walking_time_minutes": 4, "category": "short", "distance_meters": 350},
        {"from_stop_id": "TJ_BLOK_M", "to_stop_id": "MT_BLOK_M", "walking_time_minutes": 3, "category": "short", "distance_meters": 200},
        # Bundaran HI transfers
        {"from_stop_id": "TJ_BUNDARAN_HI", "to_stop_id": "MRT_BUNDARAN_HI", "walking_time_minutes": 5, "category": "short", "distance_meters": 400},
        # Tanah Abang transfers
        {"from_stop_id": "TJ_TANAH_ABANG", "to_stop_id": "KRL_TANAH_ABANG", "walking_time_minutes": 5, "category": "short", "distance_meters": 380},
        # Manggarai transfers
        {"from_stop_id": "TJ_MANGGARAI", "to_stop_id": "KRL_MANGGARAI", "walking_time_minutes": 6, "category": "short", "distance_meters": 500},
        # Harmoni transfers
        {"from_stop_id": "TJ_HARMONI", "to_stop_id": "TJ_HARMONI_CENTRAL", "walking_time_minutes": 2, "category": "short", "distance_meters": 120},
        {"from_stop_id": "TJ_HARMONI", "to_stop_id": "MT_HARMONI", "walking_time_minutes": 3, "category": "short", "distance_meters": 200},
        # Lebak Bulus transfers
        {"from_stop_id": "TJ_LEBAK_BULUS", "to_stop_id": "MRT_LEBAK_BULUS", "walking_time_minutes": 7, "category": "medium", "distance_meters": 650},
        # Cawang transfers
        {"from_stop_id": "TJ_CAWANG", "to_stop_id": "KRL_CAWANG", "walking_time_minutes": 10, "category": "long", "distance_meters": 800},
        # Kampung Bandan transfers
        {"from_stop_id": "TJ_KAMPUNG_BANDAN", "to_stop_id": "KRL_KAMPUNG_BANDAN", "walking_time_minutes": 4, "category": "short", "distance_meters": 300},
        # Senayan transfers
        {"from_stop_id": "TJ_SENAYAN", "to_stop_id": "MRT_SENAYAN", "walking_time_minutes": 4, "category": "short", "distance_meters": 320},
        # Cross-hub transfers (longer distance)
        {"from_stop_id": "KRL_SUDIRMAN", "to_stop_id": "KRL_TANAH_ABANG", "walking_time_minutes": 15, "category": "long", "distance_meters": 1200},
        {"from_stop_id": "KRL_SUDIRMAN", "to_stop_id": "KRL_MANGGARAI", "walking_time_minutes": 18, "category": "long", "distance_meters": 1500},
    ]
    return pd.DataFrame(rows)


def make_routes() -> pd.DataFrame:
    """Generate route definitions for all modes."""
    rows = [
        {"route_id": "TJ_1", "route_name": "Blok M - Kota", "mode": "Transjakarta", "total_stops": 18},
        {"route_id": "TJ_2", "route_name": "Harmoni - Senen", "mode": "Transjakarta", "total_stops": 12},
        {"route_id": "TJ_3", "route_name": "Dukuh Atas - Pulo Gadung", "mode": "Transjakarta", "total_stops": 22},
        {"route_id": "TJ_4", "route_name": "Lebak Bulus - Ragunan", "mode": "Transjakarta", "total_stops": 15},
        {"route_id": "TJ_5", "route_name": "Kampung Bandan - Pluit", "mode": "Transjakarta", "total_stops": 20},
        {"route_id": "MRT_NS", "route_name": "MRT North-South", "mode": "MRT", "total_stops": 13},
        {"route_id": "KRL_BK", "route_name": "KRL Bogor-Kota", "mode": "KRL", "total_stops": 30},
        {"route_id": "KRL_ABE", "route_name": "KRL Tanah Abang - Angke", "mode": "KRL", "total_stops": 10},
        {"route_id": "LRT_KG_V", "route_name": "LRT Kelapa Gading - Velodrome", "mode": "LRT", "total_stops": 6},
        {"route_id": "MT_LOCAL_1", "route_name": "Mikrotrans Dukuh Atas", "mode": "Mikrotrans", "total_stops": 5},
    ]
    return pd.DataFrame(rows)


def make_schedules() -> pd.DataFrame:
    """Generate realistic trip schedules with peak/off-peak headways."""
    rows = []

    # Transjakarta routes: 5-8 min peak, 10-15 min off-peak
    for route_id, route_stops in [
        ("TJ_1", ["TJ_BLOK_M", "TJ_SENAYAN", "TJ_DUKUH_ATAS"]),
        ("TJ_2", ["TJ_HARMONI", "TJ_HARMONI_CENTRAL", "TJ_DUKUH_ATAS"]),
        ("TJ_3", ["TJ_DUKUH_ATAS", "TJ_MANGGARAI", "TJ_CAWANG"]),
        ("TJ_4", ["TJ_LEBAK_BULUS", "TJ_BLOK_M", "TJ_SENAYAN"]),
        ("TJ_5", ["TJ_KAMPUNG_BANDAN", "TJ_HARMONI", "TJ_TANAH_ABANG"]),
    ]:
        for trip_idx in range(40):
            hour = 6 + trip_idx // 4
            is_peak = hour in [7, 8, 9, 16, 17, 18]
            headway = 6 if is_peak else 12
            trip_start = BASE_DATE + timedelta(minutes=trip_idx * headway)
            for seq, stop_id in enumerate(route_stops):
                arrival = trip_start + timedelta(minutes=seq * 7)
                rows.append({
                    "trip_id": f"{route_id}_{trip_idx:03d}",
                    "route_id": route_id,
                    "mode": "Transjakarta",
                    "stop_id": stop_id,
                    "stop_sequence": seq + 1,
                    "arrival_time": arrival,
                    "departure_time": arrival + timedelta(minutes=1),
                })

    # MRT: 5 min peak, 10 min off-peak
    mrt_route_stops = ["MRT_LEBAK_BULUS", "MRT_BLOK_M", "MRT_SENAYAN", "MRT_BUNDARAN_HI", "MRT_DUKUH_ATAS"]
    for trip_idx in range(50):
        hour = 6 + trip_idx // 5
        is_peak = hour in [7, 8, 9, 16, 17, 18]
        headway = 5 if is_peak else 10
        trip_start = BASE_DATE + timedelta(minutes=trip_idx * headway)
        for seq, stop_id in enumerate(mrt_route_stops):
            arrival = trip_start + timedelta(minutes=seq * 4)
            rows.append({
                "trip_id": f"MRT_NS_{trip_idx:03d}",
                "route_id": "MRT_NS",
                "mode": "MRT",
                "stop_id": stop_id,
                "stop_sequence": seq + 1,
                "arrival_time": arrival,
                "departure_time": arrival + timedelta(seconds=30),
            })

    # KRL: 6-10 min peak, 15-20 min off-peak
    krl_route_stops = ["KRL_CAWANG", "KRL_MANGGARAI", "KRL_SUDIRMAN", "KRL_TANAH_ABANG", "KRL_KAMPUNG_BANDAN"]
    for trip_idx in range(35):
        hour = 6 + trip_idx // 4
        is_peak = hour in [7, 8, 9, 16, 17, 18]
        headway = 8 if is_peak else 18
        trip_start = BASE_DATE + timedelta(minutes=trip_idx * headway + 3)
        for seq, stop_id in enumerate(krl_route_stops):
            arrival = trip_start + timedelta(minutes=seq * 6)
            rows.append({
                "trip_id": f"KRL_BK_{trip_idx:03d}",
                "route_id": "KRL_BK",
                "mode": "KRL",
                "stop_id": stop_id,
                "stop_sequence": seq + 1,
                "arrival_time": arrival,
                "departure_time": arrival + timedelta(seconds=30),
            })

    # LRT: 10 min headway
    for trip_idx in range(25):
        trip_start = BASE_DATE + timedelta(minutes=trip_idx * 10)
        rows.append({
            "trip_id": f"LRT_KG_V_{trip_idx:03d}",
            "route_id": "LRT_KG_V",
            "mode": "LRT",
            "stop_id": "LRT_VELODROME",
            "stop_sequence": 1,
            "arrival_time": trip_start,
            "departure_time": trip_start + timedelta(seconds=30),
        })

    return pd.DataFrame(rows)


def make_fleet_capacity() -> pd.DataFrame:
    """Generate per-vehicle-type fleet capacity data."""
    rows = [
        {"mode": "Transjakarta", "vehicle_type": "single_bus", "seated_capacity": 40, "standing_capacity": 40, "total_capacity": 80, "safe_speed_min_kmh": 10, "safe_speed_max_kmh": 50, "depot_id": "DEP_BLOK_M"},
        {"mode": "Transjakarta", "vehicle_type": "articulated_bus", "seated_capacity": 60, "standing_capacity": 60, "total_capacity": 120, "safe_speed_min_kmh": 10, "safe_speed_max_kmh": 50, "depot_id": "DEP_BLOK_M"},
        {"mode": "Transjakarta", "vehicle_type": "low_entry_bus", "seated_capacity": 30, "standing_capacity": 30, "total_capacity": 60, "safe_speed_min_kmh": 10, "safe_speed_max_kmh": 50, "depot_id": "DEP_HARMONI"},
        {"mode": "Transjakarta", "vehicle_type": "electric_bus", "seated_capacity": 40, "standing_capacity": 35, "total_capacity": 75, "safe_speed_min_kmh": 10, "safe_speed_max_kmh": 50, "depot_id": "DEP_LEBAK_BULUS"},
        {"mode": "MRT", "vehicle_type": "trainset_6car", "seated_capacity": 480, "standing_capacity": 720, "total_capacity": 1200, "safe_speed_min_kmh": 0, "safe_speed_max_kmh": 80, "depot_id": "DEP_MRT_LEBAK_BULUS"},
        {"mode": "KRL", "vehicle_type": "trainset_12car", "seated_capacity": 1000, "standing_capacity": 1000, "total_capacity": 2000, "safe_speed_min_kmh": 0, "safe_speed_max_kmh": 80, "depot_id": "DEP_KRL_MANGGARAI"},
        {"mode": "LRT", "vehicle_type": "trainset_2car", "seated_capacity": 140, "standing_capacity": 130, "total_capacity": 270, "safe_speed_min_kmh": 0, "safe_speed_max_kmh": 60, "depot_id": "DEP_LRT_VELODROME"},
        {"mode": "LRT", "vehicle_type": "trainset_4car", "seated_capacity": 280, "standing_capacity": 260, "total_capacity": 540, "safe_speed_min_kmh": 0, "safe_speed_max_kmh": 60, "depot_id": "DEP_LRT_VELODROME"},
        {"mode": "Mikrotrans", "vehicle_type": "microbus", "seated_capacity": 10, "standing_capacity": 5, "total_capacity": 15, "safe_speed_min_kmh": 10, "safe_speed_max_kmh": 40, "depot_id": "DEP_LOCAL"},
    ]
    return pd.DataFrame(rows)


def make_synthetic_tapin(n: int = 2500) -> pd.DataFrame:
    """Generate synthetic tap-in/tap-out records across all hubs."""
    rng = np.random.default_rng(42)
    stops = [
        "TJ_BLOK_M", "TJ_DUKUH_ATAS", "TJ_BUNDARAN_HI", "TJ_TANAH_ABANG",
        "TJ_MANGGARAI", "TJ_HARMONI", "TJ_LEBAK_BULUS", "TJ_CAWANG",
        "TJ_KAMPUNG_BANDAN", "TJ_SENAYAN",
        "MRT_DUKUH_ATAS", "MRT_BLOK_M", "MRT_BUNDARAN_HI", "MRT_LEBAK_BULUS", "MRT_SENAYAN",
        "KRL_SUDIRMAN", "KRL_TANAH_ABANG", "KRL_MANGGARAI", "KRL_CAWANG", "KRL_KAMPUNG_BANDAN",
        "LRT_VELODROME",
    ]
    weights = [
        0.15, 0.12, 0.08, 0.05, 0.05, 0.08, 0.04, 0.04, 0.03, 0.04,
        0.06, 0.04, 0.03, 0.03, 0.02,
        0.05, 0.03, 0.03, 0.02, 0.02,
        0.02,
    ]
    weights = np.array(weights) / sum(weights)

    payment_channels = ["bank_card", "qris_tap", "kmt", "app", "emoney"]
    fare_products = ["regular", "student", "senior"]

    rows = []
    for i in range(n):
        start = BASE_DATE + timedelta(minutes=int(rng.normal(180, 60)))
        hour = start.hour
        is_peak = hour in [7, 8, 9, 16, 17, 18]
        origin = rng.choice(stops, p=weights)
        dest_candidates = [s for s in stops if s != origin]
        dest = rng.choice(dest_candidates)

        if origin.startswith("TJ"):
            origin_mode = "Transjakarta"
            route_id = "TJ_1"
        elif origin.startswith("MRT"):
            origin_mode = "MRT"
            route_id = "MRT_NS"
        elif origin.startswith("KRL"):
            origin_mode = "KRL"
            route_id = "KRL_BK"
        elif origin.startswith("LRT"):
            origin_mode = "LRT"
            route_id = "LRT_KG_V"
        else:
            origin_mode = "Mikrotrans"
            route_id = "MT_LOCAL_1"

        duration = int(max(8, rng.normal(25 if is_peak else 18, 8)))
        transfer_prob = 0.35 if origin.startswith("TJ") or dest.startswith("TJ") else 0.15
        is_transfer = bool(rng.random() < transfer_prob)

        rows.append({
            "event_id": f"E{i:05d}",
            "hashed_card_id": f"u{rng.integers(1, 500):04d}",
            "mode": origin_mode,
            "operator": origin_mode,
            "route_id": route_id,
            "trip_id": None,
            "tap_in_stop_id": origin,
            "tap_in_time": start,
            "tap_out_stop_id": dest,
            "tap_out_time": start + timedelta(minutes=duration),
            "payment_channel": rng.choice(payment_channels),
            "fare_product": rng.choice(fare_products, p=[0.7, 0.2, 0.1]),
            "transfer_flag": is_transfer,
            "validation_status": "valid",
        })
    return pd.DataFrame(rows)


def make_vehicle_positions() -> pd.DataFrame:
    """Generate simulated vehicle positions for key corridors."""
    return pd.DataFrame([
        {"vehicle_id": "BUS_001", "route_id": "TJ_1", "mode": "Transjakarta", "current_stop_id": "TJ_SENAYAN", "next_stop_id": "TJ_DUKUH_ATAS", "lat": -6.2170, "lon": 106.8110, "speed_kmh": 24, "delay_minutes": 2, "occupancy": 76, "capacity": 80, "updated_at": BASE_DATE + timedelta(minutes=18)},
        {"vehicle_id": "BUS_002", "route_id": "TJ_1", "mode": "Transjakarta", "current_stop_id": "TJ_BLOK_M", "next_stop_id": "TJ_SENAYAN", "lat": -6.2380, "lon": 106.8010, "speed_kmh": 28, "delay_minutes": 0, "occupancy": 34, "capacity": 80, "updated_at": BASE_DATE + timedelta(minutes=19)},
        {"vehicle_id": "BUS_003", "route_id": "TJ_3", "mode": "Transjakarta", "current_stop_id": "TJ_MANGGARAI", "next_stop_id": "TJ_CAWANG", "lat": -6.2320, "lon": 106.8620, "speed_kmh": 22, "delay_minutes": 5, "occupancy": 92, "capacity": 120, "updated_at": BASE_DATE + timedelta(minutes=22)},
        {"vehicle_id": "BUS_004", "route_id": "TJ_2", "mode": "Transjakarta", "current_stop_id": "TJ_HARMONI", "next_stop_id": "TJ_DUKUH_ATAS", "lat": -6.1850, "lon": 106.8240, "speed_kmh": 20, "delay_minutes": 1, "occupancy": 45, "capacity": 80, "updated_at": BASE_DATE + timedelta(minutes=20)},
        {"vehicle_id": "MRT_001", "route_id": "MRT_NS", "mode": "MRT", "current_stop_id": "MRT_SENAYAN", "next_stop_id": "MRT_BUNDARAN_HI", "lat": -6.2100, "lon": 106.8125, "speed_kmh": 45, "delay_minutes": 0, "occupancy": 650, "capacity": 1200, "updated_at": BASE_DATE + timedelta(minutes=20)},
        {"vehicle_id": "MRT_002", "route_id": "MRT_NS", "mode": "MRT", "current_stop_id": "MRT_BLOK_M", "next_stop_id": "MRT_SENAYAN", "lat": -6.2350, "lon": 106.8010, "speed_kmh": 50, "delay_minutes": 1, "occupancy": 420, "capacity": 1200, "updated_at": BASE_DATE + timedelta(minutes=21)},
        {"vehicle_id": "KRL_001", "route_id": "KRL_BK", "mode": "KRL", "current_stop_id": "KRL_MANGGARAI", "next_stop_id": "KRL_SUDIRMAN", "lat": -6.2100, "lon": 106.8370, "speed_kmh": 40, "delay_minutes": 3, "occupancy": 1200, "capacity": 2000, "updated_at": BASE_DATE + timedelta(minutes=17)},
        {"vehicle_id": "KRL_002", "route_id": "KRL_BK", "mode": "KRL", "current_stop_id": "KRL_TANAH_ABANG", "next_stop_id": "KRL_KAMPUNG_BANDAN", "lat": -6.1720, "lon": 106.8230, "speed_kmh": 35, "delay_minutes": 0, "occupancy": 800, "capacity": 2000, "updated_at": BASE_DATE + timedelta(minutes=23)},
    ])


def make_incidents() -> pd.DataFrame:
    """Generate sample incidents across different hubs and severity levels."""
    return pd.DataFrame([
        {"incident_id": "INC_001", "type": "traffic_jam", "severity": "medium", "route_id": "TJ_1", "stop_id": "TJ_DUKUH_ATAS", "lat": -6.2008, "lon": 106.8228, "delay_impact_minutes": 6, "status": "active", "reported_at": BASE_DATE + timedelta(minutes=35), "description": "Kemacetan padat sekitar Dukuh Atas, volume kendaraan tinggi"},
        {"incident_id": "INC_002", "type": "flood", "severity": "low", "route_id": "TJ_3", "stop_id": "TJ_CAWANG", "lat": -6.2482, "lon": 106.8728, "delay_impact_minutes": 3, "status": "monitoring", "reported_at": BASE_DATE + timedelta(minutes=44), "description": "Genangan ringan di ruas jalan dekat Halte Cawang"},
        {"incident_id": "INC_003", "type": "signal_failure", "severity": "high", "route_id": "TJ_2", "stop_id": "TJ_HARMONI", "lat": -6.1744, "lon": 106.8258, "delay_impact_minutes": 12, "status": "active", "reported_at": BASE_DATE + timedelta(minutes=50), "description": "Gangguan sinyal ATCS di persimpangan Harmoni"},
        {"incident_id": "INC_004", "type": "vehicle_breakdown", "severity": "medium", "route_id": "TJ_4", "stop_id": "TJ_LEBAK_BULUS", "lat": -6.2865, "lon": 106.7913, "delay_impact_minutes": 8, "status": "active", "reported_at": BASE_DATE + timedelta(minutes=55), "description": "Bus mengalami kendala teknis di Halte Lebak Bulus"},
        {"incident_id": "INC_005", "type": "heavy_rain", "severity": "medium", "route_id": "TJ_5", "stop_id": "TJ_KAMPUNG_BANDAN", "lat": -6.1552, "lon": 106.8326, "delay_impact_minutes": 5, "status": "active", "reported_at": BASE_DATE + timedelta(minutes=60), "description": "Hujan deras mengurangi visibility di area Kampung Bandan"},
    ])


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    datasets = {
        "stops": make_stops(),
        "routes": make_routes(),
        "transfer_nodes": make_transfer_nodes(),
        "schedules": make_schedules(),
        "fleet_capacity": make_fleet_capacity(),
        "vehicle_positions": make_vehicle_positions(),
        "synthetic_tapin": make_synthetic_tapin(),
        "incidents": make_incidents(),
    }
    for name, df in datasets.items():
        save_table(df, PROCESSED_DIR / f"{name}.parquet")
        df.to_csv(RAW_DIR / f"{name}.csv", index=False)
    print(f"Demo data generated in {RAW_DIR} and {PROCESSED_DIR}")
    print(f"  stops: {len(datasets['stops'])} rows")
    print(f"  transfer_nodes: {len(datasets['transfer_nodes'])} rows")
    print(f"  schedules: {len(datasets['schedules'])} rows")
    print(f"  synthetic_tapin: {len(datasets['synthetic_tapin'])} rows")


if __name__ == "__main__":
    main()
