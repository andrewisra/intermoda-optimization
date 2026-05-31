"""Weather/flood data provider for training dataset generation.

Provides synthetic weather data calibrated to Jakarta's tropical monsoon climate.
"""
from __future__ import annotations

import random
from datetime import date, time

# Jakarta climate constants
WET_MONTHS = {1, 2, 3, 4, 10, 11, 12}
DRY_MONTHS = {5, 6, 7, 8, 9}
JAKARTA_TEMP_MIN = 24
JAKARTA_TEMP_MAX = 35


def is_wet_season(month: int) -> bool:
    """Jakarta wet season: October–April."""
    return month in WET_MONTHS


def assign_date(service_day_of_week: int, month_range: list[int]) -> date:
    """Pick a random date matching the service day and season."""
    candidates = [
        date(2024, m, d)
        for m in month_range
        for d in range(1, 29)
        if date(2024, m, d).weekday() == service_day_of_week
    ]
    return random.choice(candidates) if candidates else date(2024, 1, 1)


def get_weather_synthetic(d: date, t: time) -> dict:
    """Generate calibrated synthetic weather for Jakarta.

    Rainfall patterns:
    - Wet season (Oct-Apr): higher base probability
    - Afternoon peak (14:00-18:00): convective rain boost
    - Heavy rain → higher flood probability
    """
    month = d.month
    hour = t.hour

    # Base rain probability by season
    wet_base = 0.40 if is_wet_season(month) else 0.15

    # Afternoon convective rain boost
    afternoon_boost = 0.20 if 14 <= hour <= 18 else 0.0

    prob_rain = min(wet_base + afternoon_boost, 0.70)

    # Rainfall level
    if random.random() > prob_rain:
        rainfall_level = 0
    else:
        rainfall_level = random.choices([1, 1, 2, 2, 3], k=1)[0]

    # Flood probability (correlated with heavy rain)
    if rainfall_level == 3:
        prob_flood = 0.35
    elif rainfall_level == 2:
        prob_flood = 0.10
    else:
        prob_flood = 0.02
    flood_flag = 1 if random.random() < prob_flood else 0

    # Temperature: Jakarta is tropical, small variation
    temperature_c = random.randint(JAKARTA_TEMP_MIN, JAKARTA_TEMP_MAX)

    return {
        "rainfall_level": rainfall_level,
        "flood_flag": flood_flag,
        "temperature_c": temperature_c,
    }
