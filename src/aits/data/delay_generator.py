"""Calibrated synthetic delay generator for Jakarta transit.

Delay parameters calibrated from:
- Transjakarta IKP 2023: avg delay ~4-5 min
- BPS 2023: seasonal variation
- Literature: busway 40-60% less delay than mixed traffic
"""
from __future__ import annotations

import random


def get_incident_rate(route_mode: str, hour: int, rainfall_level: int) -> float:
    """Historical incident probability by route mode, hour, and weather.

    Returns a value between 0.0 and 1.0 representing P(incident).
    """
    # Base rate by mode
    base = {
        "TRANSJAKARTA": 0.03,
        "MIKROTRANS": 0.07,
        "MRT_LRT": 0.01,
        "KRL": 0.02,
    }.get(route_mode, 0.05)

    # Rush hour multiplier
    if 7 <= hour <= 9 or 16 <= hour <= 19:
        base *= 2.5
    elif 6 <= hour <= 20:
        base *= 1.5

    # Rain multiplier
    rain_mult = {0: 1.0, 1: 1.3, 2: 1.8, 3: 2.5}
    base *= rain_mult.get(rainfall_level, 1.0)

    return min(base, 1.0)


def generate_delay(
    scheduled_travel_seconds: int,
    route_mode: str,
    hour: int,
    rainfall_level: int,
    flood_flag: int,
) -> float:
    """Generate a calibrated synthetic delay in minutes.

    Delay model:
    1. Base delay proportional to scheduled travel time (mode-dependent)
    2. Rush hour additive component
    3. Weather penalty (rain + flood)
    4. Random noise
    5. Clipped to >= 0

    Calibration targets:
    - Transjakarta IKP 2023: avg delay ~4-5 min
    - Busway: 40-60% less than mixed traffic
    - Flood: +3-12 min
    """
    scheduled_min = scheduled_travel_seconds / 60.0

    # Base delay: proportional to scheduled time, mode-dependent
    if route_mode == "TRANSJAKARTA":
        base = scheduled_min * 0.12
    elif route_mode == "MIKROTRANS":
        base = scheduled_min * 0.22
    elif route_mode in ("MRT_LRT", "KRL"):
        base = scheduled_min * 0.05
    else:
        base = scheduled_min * 0.15

    # Minimum floor
    base = max(base, 0.3)

    # Rush hour additive
    if 7 <= hour <= 9 or 16 <= hour <= 19:
        base += random.uniform(1.5, 4.0)
    else:
        base += random.uniform(0.1, 0.5)

    # Weather penalty
    if flood_flag:
        base += random.uniform(3.0, 12.0)
    elif rainfall_level == 3:
        base += random.uniform(1.5, 3.5)
    elif rainfall_level == 2:
        base += random.uniform(0.8, 2.0)
    elif rainfall_level == 1:
        base += random.uniform(0.3, 1.0)

    # Random noise
    base += random.gauss(0, 0.8)

    return max(0.0, round(base, 3))
