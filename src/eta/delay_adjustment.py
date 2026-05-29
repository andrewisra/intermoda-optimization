from __future__ import annotations


def delay_from_incident(severity: str | None, base_delay_minutes: float = 0) -> float:
    severity_factor = {"low": 2, "medium": 6, "high": 12, "critical": 20}
    return float(base_delay_minutes) + severity_factor.get(str(severity).lower(), 0)


def delay_from_weather(is_heavy_rain: bool = False, is_flood: bool = False) -> float:
    delay = 0.0
    if is_heavy_rain:
        delay += 4.0
    if is_flood:
        delay += 10.0
    return delay
