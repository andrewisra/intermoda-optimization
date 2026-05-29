from __future__ import annotations

from datetime import datetime
import pandas as pd

from src.config import PROCESSED_DIR
from src.eta.baseline_eta import next_arrivals
from src.optimizer.connection_optimizer import optimize_connection, recommend_based_on_crowding
from src.density.stop_density import density_last_minutes
from src.utils import parse_time, read_table


def load_transfer_nodes() -> pd.DataFrame:
    path = PROCESSED_DIR / 'transfer_nodes.parquet'
    if not path.exists() and not path.with_suffix('.csv').exists():
        raise FileNotFoundError('No transfer nodes. Run: python scripts/bootstrap_demo.py')
    return read_table(path)


def simulate_transfer(
    from_stop_id: str,
    to_stop_id: str,
    current_time: datetime | str,
    first_mode_eta_minutes: float = 5,
    target_route_id: str | None = None,
    load_factor: float = 0.5,
) -> dict:
    current = parse_time(current_time)
    transfers = load_transfer_nodes()
    row = transfers[(transfers['from_stop_id'] == from_stop_id) & (transfers['to_stop_id'] == to_stop_id)]
    if row.empty:
        raise ValueError(f'Transfer node not found: {from_stop_id} -> {to_stop_id}')
    walking = float(row.iloc[0]['walking_time_minutes'])
    passenger_arrival = current + pd.Timedelta(minutes=first_mode_eta_minutes + walking)

    arrivals = next_arrivals(to_stop_id, passenger_arrival, route_id=target_route_id, limit=2)
    if arrivals.empty:
        return {
            'from_stop_id': from_stop_id,
            'to_stop_id': to_stop_id,
            'status': 'no_target_arrival_found',
            'message': 'Tidak ada jadwal moda lanjutan setelah penumpang tiba di titik transfer.',
        }

    next_departure = arrivals.iloc[0]['departure_time']
    next_next_departure = arrivals.iloc[1]['departure_time'] if len(arrivals) > 1 else None
    base = optimize_connection(passenger_arrival, next_departure, next_next_departure)
    next_eta = float(arrivals.iloc[1]['eta_minutes']) if len(arrivals) > 1 and pd.notna(arrivals.iloc[1]['eta_minutes']) else None
    decision = recommend_based_on_crowding(base, load_factor=load_factor, next_vehicle_eta_minutes=next_eta)
    density = density_last_minutes(from_stop_id, current_time)

    return {
        'from_stop_id': from_stop_id,
        'to_stop_id': to_stop_id,
        'current_time': current.isoformat(),
        'first_mode_eta_minutes': first_mode_eta_minutes,
        'walking_time_minutes': walking,
        'passenger_arrival_at_target': passenger_arrival.isoformat(),
        'target_next_trip_id': arrivals.iloc[0].get('trip_id'),
        'target_next_departure_time': next_departure.isoformat(),
        'decision': decision,
        'origin_density': density,
        'status': 'ok',
    }


def simulate_all_transfer_nodes(current_time: datetime | str) -> pd.DataFrame:
    transfers = load_transfer_nodes()
    rows = []
    for _, row in transfers.iterrows():
        try:
            res = simulate_transfer(row['from_stop_id'], row['to_stop_id'], current_time)
            rows.append({
                'from_stop_id': row['from_stop_id'],
                'to_stop_id': row['to_stop_id'],
                'walking_time_minutes': res.get('walking_time_minutes'),
                'waiting_time_minutes': res.get('decision', {}).get('waiting_time_minutes'),
                'decision': res.get('decision', {}).get('decision'),
                'message': res.get('decision', {}).get('message'),
                'status': res.get('status'),
            })
        except Exception as exc:
            rows.append({'from_stop_id': row['from_stop_id'], 'to_stop_id': row['to_stop_id'], 'status': 'error', 'message': str(exc)})
    return pd.DataFrame(rows)
