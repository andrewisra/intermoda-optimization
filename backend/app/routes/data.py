from fastapi import APIRouter

from backend.app.services import list_reference_data, simulator_service

router = APIRouter(prefix="/api/data", tags=["Reference Data"])


@router.get("/reference")
def get_reference_data():
    return list_reference_data()


@router.get("/simulator")
def run_simulator():
    return simulator_service()
