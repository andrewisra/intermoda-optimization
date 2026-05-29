from __future__ import annotations


def calculate_load_factor(passenger_count: int, capacity: int) -> float:
    if capacity <= 0:
        return 0.0
    return round(float(passenger_count) / float(capacity), 3)


def load_factor_level(load_factor: float) -> str:
    if load_factor < 0.5:
        return "low"
    if load_factor < 0.85:
        return "normal"
    if load_factor < 1.0:
        return "crowded"
    return "over_capacity"
