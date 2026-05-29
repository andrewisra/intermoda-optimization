from datetime import datetime, timedelta

from src.aits.data.generate_demo_data import generate_all
from src.aits.ml.train import train_all
from src.aits.optimizer.intermodal import optimize_transfer


def test_end_to_end_optimizer():
    generate_all()
    train_all()
    now = datetime(2026, 5, 23, 7, 30)
    res = optimize_transfer(
        user_id="U_STANDARD",
        from_stop_id="TJ_DUKUH_ATAS",
        to_station_id="MRT_DUKUH_ATAS",
        route_id="TJ_01",
        current_time=now,
        scheduled_non_rail_arrival=now + timedelta(minutes=8),
        traffic_level=2,
        rainfall_level=0,
        incident_flag=0,
        tap_in_count_15m=40,
        vehicle_capacity=80,
        scheduled_headway_minutes=8,
    )
    assert res.decision in {"CONNECT", "REDIRECT_NEXT_SERVICE", "HOLD_NON_RAIL", "REVIEW"}
    assert res.rail_departure_time is not None
