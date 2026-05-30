from __future__ import annotations

from src.aits.config import MAX_SAFE_SPEED_KMH, MIN_SAFE_SPEED_KMH


def recommend_safe_speed_adjustment(current_speed_kmh: float, current_eta_minutes: float, target_eta_minutes: float) -> dict:
    """Recommend a speed band, not an unsafe precise speed instruction.

    This function is intentionally conservative. It never asks a driver to exceed the safe limit.
    """
    if current_eta_minutes <= 0 or target_eta_minutes <= 0:
        return {"action": "MAINTAIN", "recommended_speed_kmh": current_speed_kmh, "message": "Invalid ETA input; maintain safe operation."}

    ratio = current_eta_minutes / target_eta_minutes
    proposed_speed = current_speed_kmh * ratio
    bounded = min(MAX_SAFE_SPEED_KMH, max(MIN_SAFE_SPEED_KMH, proposed_speed))

    if abs(target_eta_minutes - current_eta_minutes) <= 1:
        action = "MAINTAIN"
        message = "Current pace is already synchronized with the target connection."
    elif target_eta_minutes < current_eta_minutes:
        action = "SPEED_UP_WITHIN_LIMIT"
        message = "Slightly increase speed only if safe and legally allowed."
    else:
        action = "SLOW_DOWN_WITHIN_LIMIT"
        message = "Use a conservative pace to synchronize with the next fixed rail departure."

    return {"action": action, "recommended_speed_kmh": round(float(bounded), 1), "min_safe_speed_kmh": MIN_SAFE_SPEED_KMH, "max_safe_speed_kmh": MAX_SAFE_SPEED_KMH, "message": message}
