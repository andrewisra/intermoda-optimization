from __future__ import annotations

import numpy as np


def calculate_missed_connection_risk(waiting_time_minutes: float | None, density_level: str, eta_confidence: float, walking_buffer_minutes: float) -> dict:
    """Return risk score 0-100.

    Higher score means higher chance of missed connection or poor transfer experience.
    """
    if waiting_time_minutes is None:
        base = 85.0
    elif waiting_time_minutes < 0:
        base = 95.0
    elif waiting_time_minutes <= 2:
        base = 55.0
    elif waiting_time_minutes <= 5:
        base = 25.0
    elif waiting_time_minutes <= 8:
        base = 15.0
    elif waiting_time_minutes <= 12:
        base = 45.0
    else:
        base = 70.0

    density_penalty = {"LOW": 0, "MEDIUM": 8, "HIGH": 18, "OVERLOADED": 30}.get(density_level, 10)
    uncertainty_penalty = (1.0 - float(eta_confidence)) * 25.0
    walking_penalty = max(0.0, 3.0 - float(walking_buffer_minutes)) * 5.0
    score = float(np.clip(base + density_penalty + uncertainty_penalty + walking_penalty, 0, 100))

    if score < 30:
        level = "LOW"
    elif score < 65:
        level = "MEDIUM"
    else:
        level = "HIGH"
    return {"risk_score": round(score, 1), "risk_level": level}
