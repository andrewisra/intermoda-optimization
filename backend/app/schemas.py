from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class EtaRequest(BaseModel):
    route_id: str = "TJ_01"
    stop_id: str = "TJ_DUKUH_ATAS"
    hour: int = Field(default=7, ge=0, le=23)
    day_of_week: int = Field(default=1, ge=0, le=6)
    traffic_level: int = Field(default=3, ge=0, le=5)
    rainfall_level: int = Field(default=0, ge=0, le=5)
    incident_flag: int = Field(default=0, ge=0, le=1)
    passenger_density_score: float = Field(default=0.5, ge=0, le=1.5)
    scheduled_travel_minutes: float = Field(default=10, gt=0)


class DensityRequest(BaseModel):
    stop_id: str = "TJ_DUKUH_ATAS"
    route_id: str = "TJ_01"
    hour: int = Field(default=7, ge=0, le=23)
    day_of_week: int = Field(default=1, ge=0, le=6)
    tap_in_count_15m: int = Field(default=80, ge=0)
    scheduled_headway_minutes: int = Field(default=8, gt=0)
    vehicle_capacity: int = Field(default=80, gt=0)
    event_flag: int = Field(default=0, ge=0, le=1)
    rainfall_level: int = Field(default=0, ge=0, le=5)


class TransferOptimizeRequest(BaseModel):
    user_id: str = "U_STANDARD"
    from_stop_id: str = "TJ_DUKUH_ATAS"
    to_station_id: str = "MRT_DUKUH_ATAS"
    route_id: str = "TJ_01"
    current_time: datetime = datetime(2026, 5, 23, 7, 30)
    scheduled_non_rail_arrival: datetime = datetime(2026, 5, 23, 7, 38)
    traffic_level: int = Field(default=3, ge=0, le=5)
    rainfall_level: int = Field(default=0, ge=0, le=5)
    incident_flag: int = Field(default=0, ge=0, le=1)
    tap_in_count_15m: int = Field(default=80, ge=0)
    vehicle_capacity: int = Field(default=80, gt=0)
    scheduled_headway_minutes: int = Field(default=8, gt=0)
    current_speed_kmh: float = Field(default=24, gt=0)


class IncidentRequest(BaseModel):
    location_stop_id: str
    incident_type: str
    severity: int = Field(ge=1, le=5)
    description: str
