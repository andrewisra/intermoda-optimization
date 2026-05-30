from fastapi import APIRouter

from backend.app.schemas import EtaRequest, DensityRequest
from backend.app.services import predict_eta_service, predict_density_service

router = APIRouter(prefix="/api/predict", tags=["AI Prediction"])


@router.post("/eta")
def predict_eta(payload: EtaRequest):
    """AI ETA delay prediction for non-rail mode."""
    return predict_eta_service(payload.model_dump())


@router.post("/density")
def predict_density(payload: DensityRequest):
    """AI passenger density prediction."""
    return predict_density_service(payload.model_dump())
