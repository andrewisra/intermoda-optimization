from __future__ import annotations

from fastapi import APIRouter, Query
from src.density.stop_density import density_last_minutes, vehicle_load_factor, density_by_stop

router = APIRouter(prefix='/density', tags=['Density'])


@router.get('/stop')
def get_density(stop_id: str, current_time: str, window_minutes: int = 15):
    return density_last_minutes(stop_id, current_time, window_minutes)


@router.get('/by-stop')
def get_density_by_stop(start_time: str = Query('2026-05-23T07:00:00'), end_time: str = Query('2026-05-23T09:00:00')):
    df = density_by_stop(start_time, end_time)
    return df.to_dict(orient='records')


@router.get('/load-factor')
def get_load_factor(occupancy: float = Query(...), capacity: float = Query(...)):
    return vehicle_load_factor(occupancy, capacity)
