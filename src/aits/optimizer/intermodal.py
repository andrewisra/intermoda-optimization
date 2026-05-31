from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd

from src.aits.config import WAITING_TIME_TARGET_MINUTES, MAX_HOLD_MINUTES
from src.aits.data import repository as repo
from src.aits.ml.predict import registry
from src.aits.optimizer.risk import calculate_missed_connection_risk
from src.aits.optimizer.speed import recommend_safe_speed_adjustment
from src.aits.optimizer.walking_time import estimate_personalized_walking_time


@dataclass
class TransferOptimizationResult:
    decision: str
    primary_recommendation: str
    from_stop_id: str
    to_station_id: str
    rail_trip_id: str | None
    rail_departure_time: str | None
    predicted_non_rail_arrival_time: str
    personalized_walking_minutes: float
    passenger_ready_time: str
    waiting_time_minutes: float | None
    risk_score: float
    risk_level: str
    density_level: str
    eta_confidence: float
    additional_actions: list[dict]
    explanation: str


def _find_transfer(from_stop_id: str, to_station_id: str) -> pd.Series:
    transfers = repo.transfer_nodes()
    match = transfers[(transfers["from_stop_id"] == from_stop_id) & (transfers["to_station_id"] == to_station_id)]
    if match.empty:
        raise ValueError(f"Transfer node not found: {from_stop_id} -> {to_station_id}")
    return match.iloc[0]


def _find_user(user_id: str) -> pd.Series:
    users = repo.user_profiles()
    match = users[users["user_id"] == user_id]
    if match.empty:
        return pd.Series({"user_id": user_id, "walking_profile": "STANDARD", "walking_multiplier": 1.0, "consent_personalization": False})
    return match.iloc[0]


def _next_rail_departures(station_id: str, after_time: datetime, limit: int = 4) -> pd.DataFrame:
    schedule = repo.rail_schedule()
    candidates = schedule[(schedule["station_id"] == station_id) & (schedule["departure_time"] >= after_time)].sort_values("departure_time")
    return candidates.head(limit)


def optimize_transfer(
    *,
    user_id: str,
    from_stop_id: str,
    to_station_id: str,
    route_id: str,
    current_time: datetime,
    scheduled_non_rail_arrival: datetime,
    traffic_level: int,
    rainfall_level: int,
    incident_flag: int,
    tap_in_count_15m: int,
    vehicle_capacity: int,
    scheduled_headway_minutes: int,
    current_speed_kmh: float = 24.0,
) -> TransferOptimizationResult:
    transfer = _find_transfer(from_stop_id, to_station_id)
    user = _find_user(user_id)

    scheduled_travel_seconds = max(60, int((scheduled_non_rail_arrival - current_time).total_seconds()))
    density_features = {
        "from_stop_id": from_stop_id,
        "route_id": route_id,
        "headway_minutes": float(scheduled_headway_minutes),
        "vehicle_capacity": vehicle_capacity,
        "hour": current_time.hour,
        "day_of_week": current_time.weekday(),
        "rainfall_level": rainfall_level,
        "flood_flag": 0,
        "event_flag": 0,
    }
    density = registry.predict_density(density_features)
    eta_features = {
        "route_id": route_id,
        "from_stop_id": from_stop_id,
        "to_stop_id": to_station_id,
        "route_mode": "TRANSJAKARTA",
        "scheduled_travel_seconds": scheduled_travel_seconds,
        "headway_minutes": float(scheduled_headway_minutes),
        "hour": current_time.hour,
        "day_of_week": current_time.weekday(),
        "rainfall_level": rainfall_level,
        "flood_flag": 0,
        "temperature_c": 28,
        "historical_incident_rate": 0.05,
    }
    eta = registry.predict_eta_delay(eta_features)
    predicted_arrival = current_time + timedelta(minutes=eta.predicted_eta_minutes)

    walking = estimate_personalized_walking_time(
        float(transfer["default_walking_minutes"]),
        str(user["walking_profile"]),
        bool(user["consent_personalization"]),
        str(transfer["walking_category"]),
    )
    passenger_ready = predicted_arrival + timedelta(minutes=walking.personalized_minutes)

    rail_options = _next_rail_departures(to_station_id, current_time, limit=8)
    if rail_options.empty:
        return TransferOptimizationResult(
            decision="NO_RAIL_SERVICE",
            primary_recommendation="No fixed rail departure is available in the demo schedule.",
            from_stop_id=from_stop_id,
            to_station_id=to_station_id,
            rail_trip_id=None,
            rail_departure_time=None,
            predicted_non_rail_arrival_time=predicted_arrival.isoformat(),
            personalized_walking_minutes=walking.personalized_minutes,
            passenger_ready_time=passenger_ready.isoformat(),
            waiting_time_minutes=None,
            risk_score=100,
            risk_level="HIGH",
            density_level=density.density_level,
            eta_confidence=eta.confidence_score,
            additional_actions=[],
            explanation="No rail service found. Rail schedule remains fixed and cannot be created by the optimizer.",
        )

    # Select the first rail departure that is not missed.
    feasible = rail_options[rail_options["departure_time"] >= passenger_ready]
    if feasible.empty:
        selected = rail_options.iloc[-1]
    else:
        selected = feasible.iloc[0]
    rail_departure = selected["departure_time"].to_pydatetime()
    waiting_time = (rail_departure - passenger_ready).total_seconds() / 60.0
    walking_buffer = waiting_time

    risk = calculate_missed_connection_risk(waiting_time, density.density_level, eta.confidence_score, walking_buffer)
    additional_actions: list[dict] = []

    # Core decision hierarchy.
    required_hold = max(0.0, (passenger_ready - rail_departure).total_seconds() / 60.0)
    if 0 <= waiting_time <= WAITING_TIME_TARGET_MINUTES:
        decision = "CONNECT"
        recommendation = "Connection is feasible. Recommend this fixed rail departure."
    elif waiting_time < 0:
        # This is theoretically rare because selected feasible is chosen, but kept for safety.
        if required_hold <= MAX_HOLD_MINUTES and density.density_level not in {"HIGH", "OVERLOADED"}:
            decision = "HOLD_NON_RAIL"
            recommendation = f"Hold the non-rail feeder up to {required_hold:.1f} minutes if operationally safe. Rail schedule remains unchanged."
        else:
            decision = "REDIRECT_NEXT_SERVICE"
            recommendation = "Do not chase the missed fixed rail departure. Redirect passenger to the next feasible service."
    elif waiting_time > WAITING_TIME_TARGET_MINUTES:
        decision = "REDIRECT_NEXT_SERVICE"
        recommendation = "Waiting time exceeds target. Recommend a better next service or adjust non-rail dispatch."
        speed = recommend_safe_speed_adjustment(current_speed_kmh, eta.predicted_eta_minutes, max(1.0, eta.predicted_eta_minutes + min(waiting_time - WAITING_TIME_TARGET_MINUTES, 5)))
        additional_actions.append({"type": "SAFE_SPEED_ADJUSTMENT", **speed})
    else:
        decision = "REVIEW"
        recommendation = "Manual operator review recommended."

    if density.density_level in {"HIGH", "OVERLOADED"}:
        additional_actions.append({
            "type": "DISPATCH_EXTRA_FLEET",
            "message": "Crowding is high. Prepare or dispatch the next non-rail fleet earlier if available.",
            "density_level": density.density_level,
            "load_factor_estimate": density.load_factor_estimate,
        })

    explanation = (
        f"Rail departure is treated as fixed anchor at {rail_departure.strftime('%H:%M')}. "
        f"AI predicts non-rail arrival at {predicted_arrival.strftime('%H:%M')}. "
        f"Personalized walking time is {walking.personalized_minutes} minutes. "
        f"Passenger is ready at {passenger_ready.strftime('%H:%M')}; waiting time is {waiting_time:.1f} minutes."
    )

    return TransferOptimizationResult(
        decision=decision,
        primary_recommendation=recommendation,
        from_stop_id=from_stop_id,
        to_station_id=to_station_id,
        rail_trip_id=str(selected["trip_id"]),
        rail_departure_time=rail_departure.isoformat(),
        predicted_non_rail_arrival_time=predicted_arrival.isoformat(),
        personalized_walking_minutes=walking.personalized_minutes,
        passenger_ready_time=passenger_ready.isoformat(),
        waiting_time_minutes=round(float(waiting_time), 2),
        risk_score=float(risk["risk_score"]),
        risk_level=str(risk["risk_level"]),
        density_level=density.density_level,
        eta_confidence=eta.confidence_score,
        additional_actions=additional_actions,
        explanation=explanation,
    )
