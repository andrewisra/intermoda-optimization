from __future__ import annotations

from fastapi import APIRouter
from backend.app.models.schemas import IncidentRequest
from src.incident.incident_report import report_incident, active_incidents, resolve_incident

router = APIRouter(prefix='/incidents', tags=['Incidents'])


@router.get('/active')
def list_active(route_id: str | None = None):
    return active_incidents(route_id=route_id)


@router.post('/report')
def create_incident(req: IncidentRequest):
    return report_incident(req.incident_type, req.severity, req.route_id, req.stop_id, req.lat, req.lon, req.delay_impact_minutes, req.description)


@router.post('/resolve/{incident_id}')
def resolve(incident_id: str):
    return resolve_incident(incident_id)
