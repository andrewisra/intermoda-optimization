from __future__ import annotations

from dataclasses import dataclass

from src.aits.config import USER_WALKING_PROFILES


@dataclass
class WalkingTimeResult:
    default_minutes: float
    multiplier: float
    personalized_minutes: float
    consent_used: bool
    category: str


def estimate_personalized_walking_time(default_minutes: float, walking_profile: str = "STANDARD", consent: bool = False, category: str = "UNKNOWN") -> WalkingTimeResult:
    if consent:
        multiplier = USER_WALKING_PROFILES.get(walking_profile.upper(), 1.0)
        consent_used = True
    else:
        multiplier = 1.0
        consent_used = False
    personalized = float(default_minutes) * float(multiplier)
    return WalkingTimeResult(
        default_minutes=round(float(default_minutes), 2),
        multiplier=round(float(multiplier), 2),
        personalized_minutes=round(personalized, 2),
        consent_used=consent_used,
        category=category,
    )
