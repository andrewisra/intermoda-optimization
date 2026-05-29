from __future__ import annotations

from datetime import datetime, timedelta
from src.config import MAX_WAITING_MINUTES, MAX_DWELL_EXTENSION_MINUTES
from src.utils import parse_time


def optimize_connection(
    passenger_arrival_time: datetime | str,
    next_vehicle_departure_time: datetime | str,
    next_next_vehicle_departure_time: datetime | str | None = None,
    max_waiting_minutes: float = MAX_WAITING_MINUTES,
    max_dwell_extension_minutes: float = MAX_DWELL_EXTENSION_MINUTES,
) -> dict:
    passenger_arrival = parse_time(passenger_arrival_time)
    departure = parse_time(next_vehicle_departure_time)
    waiting = (departure - passenger_arrival).total_seconds() / 60

    if 0 <= waiting <= max_waiting_minutes:
        return {'decision': 'connect', 'waiting_time_minutes': round(waiting, 2), 'dwell_extension_minutes': 0, 'message': 'Koneksi antarmoda feasible. Waiting time masih di bawah threshold.'}

    if waiting < 0:
        required_hold = abs(waiting)
        if required_hold <= max_dwell_extension_minutes:
            return {'decision': 'hold_vehicle', 'waiting_time_minutes': 0, 'dwell_extension_minutes': round(required_hold, 2), 'message': f'Moda lanjutan disarankan menahan keberangkatan {required_hold:.1f} menit.'}
        if next_next_vehicle_departure_time:
            next_wait = (parse_time(next_next_vehicle_departure_time) - passenger_arrival).total_seconds() / 60
            if 0 <= next_wait <= max_waiting_minutes:
                return {'decision': 'take_next_vehicle', 'waiting_time_minutes': round(next_wait, 2), 'dwell_extension_minutes': 0, 'message': 'Moda terdekat sudah tidak feasible. Arahkan penumpang ke moda berikutnya.'}
        return {'decision': 'missed_connection', 'waiting_time_minutes': None, 'dwell_extension_minutes': 0, 'message': 'Koneksi terlewat dan tidak ada opsi moda berikutnya yang memenuhi threshold.'}

    return {'decision': 'wait_or_rebalance', 'waiting_time_minutes': round(waiting, 2), 'dwell_extension_minutes': 0, 'message': 'Waiting time melebihi threshold. Perlu optimasi headway, dispatch, atau rekomendasi moda alternatif.'}


def recommend_based_on_crowding(base_decision: dict, load_factor: float, next_vehicle_eta_minutes: float | None) -> dict:
    result = dict(base_decision)
    if load_factor >= 0.9 and next_vehicle_eta_minutes is not None and next_vehicle_eta_minutes <= MAX_WAITING_MINUTES:
        result['decision'] = 'distribute_to_next_vehicle'
        result['message'] = 'Moda pertama sangat padat. Sebagian penumpang direkomendasikan menunggu moda berikutnya yang masih di bawah threshold.'
        result['crowding_action'] = 'split_demand'
    else:
        result['crowding_action'] = 'none'
    result['load_factor'] = round(load_factor, 3)
    return result


def passenger_arrival_at_next_mode(first_mode_eta, walking_time_minutes: float):
    return parse_time(first_mode_eta) + timedelta(minutes=float(walking_time_minutes))
