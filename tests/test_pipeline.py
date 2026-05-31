from datetime import datetime, timedelta

from src.aits.data.generate_demo_data import generate_all
from src.aits.optimizer.intermodal import optimize_transfer


def test_end_to_end_optimizer():
    """Test optimizer with demo data. Training is covered by dedicated test files."""
    generate_all()
    # NOTE: train_all() is NOT called here — it runs 50+50 Optuna trials.
    # Training is covered by test_train_eta.py and test_train_density.py.
    # The optimizer works with the demo data structure, not the trained models.
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
