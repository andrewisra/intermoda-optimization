from __future__ import annotations

from datetime import datetime, timedelta
import random
import pandas as pd

from src.config import RAW_DIR, PROCESSED_DIR
from src.utils import save_table

BASE_DATE = datetime(2026, 5, 23, 7, 0, 0)


def generate_stops() -> pd.DataFrame:
    return pd.DataFrame([
        {'stop_id': 'TJ_BLOK_M', 'stop_name': 'Halte Transjakarta Blok M', 'mode': 'Transjakarta', 'lat': -6.2445, 'lon': 106.8007},
        {'stop_id': 'TJ_SENAYAN', 'stop_name': 'Halte Transjakarta Senayan', 'mode': 'Transjakarta', 'lat': -6.2274, 'lon': 106.8017},
        {'stop_id': 'TJ_DUKUH_ATAS', 'stop_name': 'Halte Transjakarta Dukuh Atas', 'mode': 'Transjakarta', 'lat': -6.2003, 'lon': 106.8227},
        {'stop_id': 'MRT_BLOK_M', 'stop_name': 'Stasiun MRT Blok M', 'mode': 'MRT', 'lat': -6.2440, 'lon': 106.7989},
        {'stop_id': 'MRT_SENAYAN', 'stop_name': 'Stasiun MRT Senayan', 'mode': 'MRT', 'lat': -6.2264, 'lon': 106.8023},
        {'stop_id': 'MRT_DUKUH_ATAS', 'stop_name': 'Stasiun MRT Dukuh Atas BNI', 'mode': 'MRT', 'lat': -6.2001, 'lon': 106.8231},
        {'stop_id': 'KRL_SUDIRMAN', 'stop_name': 'Stasiun KRL Sudirman', 'mode': 'KRL', 'lat': -6.2027, 'lon': 106.8235},
        {'stop_id': 'TJ_CAWANG', 'stop_name': 'Halte Transjakarta Cawang', 'mode': 'Transjakarta', 'lat': -6.2482, 'lon': 106.8728},
        {'stop_id': 'KRL_CAWANG', 'stop_name': 'Stasiun KRL Cawang', 'mode': 'KRL', 'lat': -6.2429, 'lon': 106.8589},
    ])


def generate_routes() -> pd.DataFrame:
    return pd.DataFrame([
        {'route_id': 'TJ_1', 'route_name': 'Blok M - Kota', 'mode': 'Transjakarta'},
        {'route_id': 'MRT_NS', 'route_name': 'MRT North-South', 'mode': 'MRT'},
        {'route_id': 'KRL_BK', 'route_name': 'KRL Bogor-Kota', 'mode': 'KRL'},
    ])


def generate_stop_times() -> pd.DataFrame:
    rows = []
    for trip_idx in range(12):
        trip_start = BASE_DATE + timedelta(minutes=10 * trip_idx)
        for seq, stop_id in enumerate(['TJ_BLOK_M', 'TJ_SENAYAN', 'TJ_DUKUH_ATAS']):
            arrival = trip_start + timedelta(minutes=seq * 8)
            rows.append({'trip_id': f'TJ_1_{trip_idx:02d}', 'route_id': 'TJ_1', 'stop_id': stop_id, 'stop_sequence': seq + 1, 'arrival_time': arrival, 'departure_time': arrival + timedelta(minutes=1), 'mode': 'Transjakarta'})
    for trip_idx in range(14):
        trip_start = BASE_DATE + timedelta(minutes=5 + 8 * trip_idx)
        for seq, stop_id in enumerate(['MRT_BLOK_M', 'MRT_SENAYAN', 'MRT_DUKUH_ATAS']):
            arrival = trip_start + timedelta(minutes=seq * 6)
            rows.append({'trip_id': f'MRT_NS_{trip_idx:02d}', 'route_id': 'MRT_NS', 'stop_id': stop_id, 'stop_sequence': seq + 1, 'arrival_time': arrival, 'departure_time': arrival + timedelta(minutes=1), 'mode': 'MRT'})
    for trip_idx in range(10):
        trip_start = BASE_DATE + timedelta(minutes=6 + 12 * trip_idx)
        for seq, stop_id in enumerate(['KRL_CAWANG', 'KRL_SUDIRMAN']):
            arrival = trip_start + timedelta(minutes=seq * 14)
            rows.append({'trip_id': f'KRL_BK_{trip_idx:02d}', 'route_id': 'KRL_BK', 'stop_id': stop_id, 'stop_sequence': seq + 1, 'arrival_time': arrival, 'departure_time': arrival + timedelta(minutes=1), 'mode': 'KRL'})
    return pd.DataFrame(rows)


def generate_transfer_nodes() -> pd.DataFrame:
    return pd.DataFrame([
        {'from_stop_id': 'TJ_DUKUH_ATAS', 'to_stop_id': 'MRT_DUKUH_ATAS', 'walking_time_minutes': 5, 'category': 'short'},
        {'from_stop_id': 'TJ_DUKUH_ATAS', 'to_stop_id': 'KRL_SUDIRMAN', 'walking_time_minutes': 7, 'category': 'medium'},
        {'from_stop_id': 'TJ_SENAYAN', 'to_stop_id': 'MRT_SENAYAN', 'walking_time_minutes': 4, 'category': 'short'},
        {'from_stop_id': 'TJ_CAWANG', 'to_stop_id': 'KRL_CAWANG', 'walking_time_minutes': 10, 'category': 'medium'},
    ])


def generate_fleet_capacity() -> pd.DataFrame:
    return pd.DataFrame([
        {'mode': 'Transjakarta', 'vehicle_type': 'single_bus', 'total_capacity': 80, 'safe_speed_min_kmh': 10, 'safe_speed_max_kmh': 50},
        {'mode': 'Transjakarta', 'vehicle_type': 'articulated_bus', 'total_capacity': 120, 'safe_speed_min_kmh': 10, 'safe_speed_max_kmh': 50},
        {'mode': 'MRT', 'vehicle_type': 'trainset', 'total_capacity': 1200, 'safe_speed_min_kmh': 0, 'safe_speed_max_kmh': 80},
        {'mode': 'KRL', 'vehicle_type': 'trainset', 'total_capacity': 2000, 'safe_speed_min_kmh': 0, 'safe_speed_max_kmh': 80},
        {'mode': 'Mikrotrans', 'vehicle_type': 'microbus', 'total_capacity': 15, 'safe_speed_min_kmh': 10, 'safe_speed_max_kmh': 40},
    ])


def generate_vehicle_positions() -> pd.DataFrame:
    return pd.DataFrame([
        {'vehicle_id': 'BUS_001', 'route_id': 'TJ_1', 'mode': 'Transjakarta', 'current_stop_id': 'TJ_SENAYAN', 'next_stop_id': 'TJ_DUKUH_ATAS', 'lat': -6.2170, 'lon': 106.8110, 'speed_kmh': 24, 'delay_minutes': 2, 'occupancy': 76, 'capacity': 80, 'updated_at': BASE_DATE + timedelta(minutes=18)},
        {'vehicle_id': 'BUS_002', 'route_id': 'TJ_1', 'mode': 'Transjakarta', 'current_stop_id': 'TJ_BLOK_M', 'next_stop_id': 'TJ_SENAYAN', 'lat': -6.2380, 'lon': 106.8010, 'speed_kmh': 28, 'delay_minutes': 0, 'occupancy': 34, 'capacity': 80, 'updated_at': BASE_DATE + timedelta(minutes=19)},
        {'vehicle_id': 'MRT_001', 'route_id': 'MRT_NS', 'mode': 'MRT', 'current_stop_id': 'MRT_SENAYAN', 'next_stop_id': 'MRT_DUKUH_ATAS', 'lat': -6.2200, 'lon': 106.8092, 'speed_kmh': 45, 'delay_minutes': 0, 'occupancy': 650, 'capacity': 1200, 'updated_at': BASE_DATE + timedelta(minutes=20)},
    ])


def generate_synthetic_tapin() -> pd.DataFrame:
    random.seed(42)
    stops = ['TJ_BLOK_M', 'TJ_SENAYAN', 'TJ_DUKUH_ATAS', 'MRT_DUKUH_ATAS', 'KRL_SUDIRMAN']
    rows = []
    for idx in range(250):
        start = BASE_DATE + timedelta(minutes=random.randint(0, 120))
        origin = random.choices(stops, weights=[35, 20, 20, 15, 10])[0]
        dest = random.choice([s for s in stops if s != origin])
        rows.append({'event_id': idx + 1, 'hashed_card_id': f'user_{random.randint(1, 120):03d}', 'mode': 'Transjakarta' if origin.startswith('TJ') else ('MRT' if origin.startswith('MRT') else 'KRL'), 'route_id': 'TJ_1' if origin.startswith('TJ') else ('MRT_NS' if origin.startswith('MRT') else 'KRL_BK'), 'tap_in_stop_id': origin, 'tap_in_time': start, 'tap_out_stop_id': dest, 'tap_out_time': start + timedelta(minutes=random.randint(8, 45)), 'transfer_flag': random.choice([0, 0, 0, 1])})
    return pd.DataFrame(rows)


def generate_incidents() -> pd.DataFrame:
    return pd.DataFrame([
        {'incident_id': 'INC_001', 'type': 'traffic_jam', 'severity': 'medium', 'route_id': 'TJ_1', 'stop_id': 'TJ_SENAYAN', 'lat': -6.225, 'lon': 106.803, 'delay_impact_minutes': 4, 'status': 'active', 'reported_at': BASE_DATE + timedelta(minutes=30), 'description': 'Kemacetan padat.'},
        {'incident_id': 'INC_002', 'type': 'flood', 'severity': 'low', 'route_id': 'TJ_1', 'stop_id': 'TJ_CAWANG', 'lat': -6.248, 'lon': 106.872, 'delay_impact_minutes': 2, 'status': 'monitoring', 'reported_at': BASE_DATE + timedelta(minutes=44), 'description': 'Genangan ringan.'},
    ])


def main() -> None:
    datasets = {
        'stops': generate_stops(),
        'routes': generate_routes(),
        'stop_times': generate_stop_times(),
        'transfer_nodes': generate_transfer_nodes(),
        'fleet_capacity': generate_fleet_capacity(),
        'vehicle_positions': generate_vehicle_positions(),
        'synthetic_tapin': generate_synthetic_tapin(),
        'incidents': generate_incidents(),
    }
    for name, df in datasets.items():
        save_table(df, PROCESSED_DIR / f'{name}.parquet')
        df.to_csv(RAW_DIR / f'{name}.csv', index=False)
    print(f'Generated sample data into {PROCESSED_DIR}')


if __name__ == '__main__':
    main()
