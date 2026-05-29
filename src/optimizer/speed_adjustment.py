from __future__ import annotations

from src.config import MIN_SAFE_SPEED_KMH, MAX_SAFE_SPEED_KMH


def recommend_speed_adjustment(
    current_speed_kmh: float,
    current_eta_minutes: float,
    target_arrival_in_minutes: float,
    min_safe_speed_kmh: float = MIN_SAFE_SPEED_KMH,
    max_safe_speed_kmh: float = MAX_SAFE_SPEED_KMH,
) -> dict:
    if current_eta_minutes <= 0 or current_speed_kmh <= 0:
        return {'action': 'hold', 'recommended_speed_kmh': current_speed_kmh, 'message': 'Data ETA/kecepatan tidak valid.'}
    ratio = current_eta_minutes / target_arrival_in_minutes if target_arrival_in_minutes > 0 else 1
    recommended_speed = current_speed_kmh * ratio
    clipped_speed = min(max(recommended_speed, min_safe_speed_kmh), max_safe_speed_kmh)
    if clipped_speed > current_speed_kmh + 2:
        action = 'increase_speed_within_safety_limit'
    elif clipped_speed < current_speed_kmh - 2:
        action = 'reduce_speed_to_sync_connection'
    else:
        action = 'maintain_speed'
    return {'action': action, 'current_speed_kmh': round(current_speed_kmh, 2), 'recommended_speed_kmh': round(clipped_speed, 2), 'raw_recommended_speed_kmh': round(recommended_speed, 2), 'safety_min_kmh': min_safe_speed_kmh, 'safety_max_kmh': max_safe_speed_kmh, 'message': 'Rekomendasi kecepatan dihitung dalam rentang keselamatan operasional.'}

# Backward-compatible alias for older imports.
def recommend_speed(current_distance_km: float, target_arrival_minutes: float, current_speed_kmh: float) -> dict:
    current_eta_minutes = current_distance_km / current_speed_kmh * 60 if current_speed_kmh else 0
    return recommend_speed_adjustment(current_speed_kmh, current_eta_minutes, target_arrival_minutes)
