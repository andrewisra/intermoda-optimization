from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional


class ETAResponse(BaseModel):
    stop_id: str
    route_id: Optional[str] = None
    eta_minutes: Optional[float] = None
    arrival_time: Optional[str] = None
    status: str


class TransferRequest(BaseModel):
    from_stop_id: str = Field(..., examples=['TJ_DUKUH_ATAS'])
    to_stop_id: str = Field(..., examples=['MRT_DUKUH_ATAS'])
    current_time: str = Field(..., examples=['2026-05-23T07:20:00'])
    first_mode_eta_minutes: float = 5
    target_route_id: Optional[str] = None
    load_factor: float = 0.5


class IncidentRequest(BaseModel):
    incident_type: str = 'traffic_jam'
    severity: str = 'medium'
    route_id: str
    stop_id: str
    lat: float
    lon: float
    delay_impact_minutes: float = 3
    description: str = ''


class SpeedAdjustmentRequest(BaseModel):
    current_speed_kmh: float
    current_eta_minutes: float
    target_arrival_in_minutes: float
