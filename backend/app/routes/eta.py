from __future__ import annotations

from fastapi import APIRouter, Query
from src.eta.baseline_eta import estimate_eta_with_incident, next_arrivals

router = APIRouter(prefix='/eta', tags=['ETA'])


@router.get('/next')
def get_eta(stop_id: str = Query(...), current_time: str = Query(...), route_id: str | None = Query(default=None)):
    return estimate_eta_with_incident(stop_id=stop_id, current_time=current_time, route_id=route_id)


@router.get('/arrivals')
def get_next_arrivals(stop_id: str, current_time: str, route_id: str | None = None, limit: int = 5):
    df = next_arrivals(stop_id, current_time, route_id=route_id, limit=limit)
    return df.to_dict(orient='records')
