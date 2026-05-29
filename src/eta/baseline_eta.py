from __future__ import annotations

from datetime import datetime
import pandas as pd

from src.config import PROCESSED_DIR
from src.utils import parse_time, read_table


def load_stop_times() -> pd.DataFrame:
    for name in ['stop_times', 'schedules', 'gtfs_stop_times']:
        path = PROCESSED_DIR / f'{name}.parquet'
        if path.exists() or path.with_suffix('.csv').exists():
            df = read_table(path)
            df['arrival_time'] = pd.to_datetime(df['arrival_time'])
            df['departure_time'] = pd.to_datetime(df['departure_time'])
            return df
    raise FileNotFoundError('No stop_times data. Run: python scripts/bootstrap_demo.py')


def next_arrivals(stop_id: str, after_time: datetime | str, route_id: str | None = None, limit: int = 5) -> pd.DataFrame:
    stop_times = load_stop_times()
    after = parse_time(after_time)
    mask = (stop_times['stop_id'].astype(str) == str(stop_id)) & (stop_times['arrival_time'] >= after)
    if route_id:
        mask &= stop_times['route_id'].astype(str).eq(str(route_id))
    result = stop_times.loc[mask].sort_values('arrival_time').head(limit).copy()
    if result.empty:
        return result
    result['eta_minutes'] = (result['arrival_time'] - after).dt.total_seconds() / 60
    return result


def estimate_eta(stop_id: str, current_time: datetime | str, route_id: str | None = None, delay_minutes: float = 0) -> dict:
    arrivals = next_arrivals(stop_id, current_time, route_id, limit=1)
    if arrivals.empty:
        return {'stop_id': stop_id, 'route_id': route_id, 'eta_minutes': None, 'arrival_time': None, 'status': 'no_scheduled_arrival_found'}
    row = arrivals.iloc[0]
    adjusted_arrival = row['arrival_time'] + pd.Timedelta(minutes=delay_minutes)
    eta = (adjusted_arrival - parse_time(current_time)).total_seconds() / 60
    return {
        'stop_id': stop_id,
        'route_id': row.get('route_id', route_id),
        'trip_id': row.get('trip_id'),
        'eta_minutes': round(max(eta, 0), 2),
        'scheduled_arrival_time': row['arrival_time'].isoformat(),
        'arrival_time': adjusted_arrival.isoformat(),
        'delay_minutes': delay_minutes,
        'status': 'ok',
    }


def estimate_eta_with_incident(stop_id: str, current_time: datetime | str, route_id: str | None = None) -> dict:
    delay = 0.0
    incidents_path = PROCESSED_DIR / 'incidents.parquet'
    if incidents_path.exists() or incidents_path.with_suffix('.csv').exists():
        incidents = read_table(incidents_path)
        active = incidents[incidents['status'].isin(['active', 'monitoring'])]
        if route_id and 'route_id' in active.columns:
            active = active[active['route_id'].astype(str).eq(str(route_id))]
        if not active.empty:
            delay = float(active['delay_impact_minutes'].max())
    return estimate_eta(stop_id, current_time, route_id, delay_minutes=delay)
