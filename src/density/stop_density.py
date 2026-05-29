from __future__ import annotations

from datetime import datetime, timedelta
import pandas as pd

from src.config import PROCESSED_DIR
from src.utils import parse_time, read_table


def load_tapin() -> pd.DataFrame:
    path = PROCESSED_DIR / 'synthetic_tapin.parquet'
    if not path.exists() and not path.with_suffix('.csv').exists():
        raise FileNotFoundError('No synthetic tap-in data. Run: python scripts/bootstrap_demo.py')
    df = read_table(path)
    df['tap_in_time'] = pd.to_datetime(df['tap_in_time'])
    df['tap_out_time'] = pd.to_datetime(df['tap_out_time'])
    return df


def calculate_stop_density(stop_id: str, start_time: datetime | str, end_time: datetime | str) -> dict:
    tap = load_tapin()
    start = parse_time(start_time)
    end = parse_time(end_time)
    mask = (tap['tap_in_stop_id'].astype(str) == str(stop_id)) & (tap['tap_in_time'] >= start) & (tap['tap_in_time'] <= end)
    count = int(tap.loc[mask].shape[0])
    if count >= 60:
        level = 'very_high'
    elif count >= 35:
        level = 'high'
    elif count >= 15:
        level = 'medium'
    else:
        level = 'low'
    return {'stop_id': stop_id, 'start_time': start.isoformat(), 'end_time': end.isoformat(), 'tap_in_count': count, 'density_level': level}


def density_last_minutes(stop_id: str, current_time: datetime | str, window_minutes: int = 15) -> dict:
    current = parse_time(current_time)
    return calculate_stop_density(stop_id, current - timedelta(minutes=window_minutes), current)


def density_by_stop(start_time: datetime | str, end_time: datetime | str) -> pd.DataFrame:
    tap = load_tapin()
    start = parse_time(start_time)
    end = parse_time(end_time)
    mask = (tap['tap_in_time'] >= start) & (tap['tap_in_time'] <= end)
    out = tap.loc[mask].groupby('tap_in_stop_id').size().reset_index(name='tap_in_count')
    def level(count: int) -> str:
        if count >= 60:
            return 'very_high'
        if count >= 35:
            return 'high'
        if count >= 15:
            return 'medium'
        return 'low'
    out['density_level'] = out['tap_in_count'].apply(level)
    return out.sort_values('tap_in_count', ascending=False)


def vehicle_load_factor(occupancy: float, capacity: float) -> dict:
    load_factor = occupancy / capacity if capacity else 0
    if load_factor >= 0.9:
        level = 'full'
    elif load_factor >= 0.7:
        level = 'crowded'
    elif load_factor >= 0.4:
        level = 'normal'
    else:
        level = 'available'
    return {'occupancy': occupancy, 'capacity': capacity, 'load_factor': round(load_factor, 3), 'level': level}
