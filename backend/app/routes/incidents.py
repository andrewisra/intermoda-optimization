from fastapi import APIRouter

from backend.app.schemas import IncidentRequest
from backend.app.services import create_incident

router = APIRouter(prefix="/api/incidents", tags=["Incident Reporting"])


@router.post("")
def report_incident(payload: IncidentRequest):
    return create_incident(payload.model_dump())
