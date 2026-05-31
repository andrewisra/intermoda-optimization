from __future__ import annotations

from datetime import datetime, timedelta
import pandas as pd

from src.aits.optimizer.intermodal import optimize_transfer


def run_demo_scenarios() -> pd.DataFrame:
    scenarios = [
        {"name": "Normal - standard walker", "user_id": "U_STANDARD", "traffic_level": 2, "rainfall_level": 0, "incident_flag": 0, "tap_in_count_15m": 45},
        {"name": "Rush hour - relaxed walker", "user_id": "U_RELAXED", "traffic_level": 4, "rainfall_level": 1, "incident_flag": 0, "tap_in_count_15m": 92},
        {"name": "Incident - assisted mobility", "user_id": "U_ASSISTED", "traffic_level": 5, "rainfall_level": 2, "incident_flag": 1, "tap_in_count_15m": 110},
        {"name": "Fast walker - low density", "user_id": "U_FAST", "traffic_level": 1, "rainfall_level": 0, "incident_flag": 0, "tap_in_count_15m": 25},
    ]
    rows = []
    now = datetime(2026, 5, 23, 7, 30)
    for s in scenarios:
        res = optimize_transfer(
            user_id=s["user_id"],
            from_stop_id="TJ_DUKUH_ATAS",
            to_station_id="MRT_DUKUH_ATAS",
            route_id="TJ_01",
            current_time=now,
            scheduled_non_rail_arrival=now + timedelta(minutes=8),
            traffic_level=s["traffic_level"],
            rainfall_level=s["rainfall_level"],
            incident_flag=s["incident_flag"],
            tap_in_count_15m=s["tap_in_count_15m"],
            vehicle_capacity=80,
            scheduled_headway_minutes=8,
        )
        rows.append({
            "scenario": s["name"],
            "decision": res.decision,
            "waiting_time_minutes": res.waiting_time_minutes,
            "risk_score": res.risk_score,
            "risk_level": res.risk_level,
            "density_level": res.density_level,
            "recommendation": res.primary_recommendation,
        })
    return pd.DataFrame(rows)
