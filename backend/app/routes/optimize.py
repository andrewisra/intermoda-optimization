from fastapi import APIRouter

from backend.app.schemas import TransferOptimizeRequest
from backend.app.services import optimize_transfer_service

router = APIRouter(prefix="/api/optimize", tags=["Intermodal Optimization"])


@router.post("/transfer")
def optimize_transfer(payload: TransferOptimizeRequest):
    """Rail-fixed intermodal optimizer. Rail schedule is never modified."""
    return optimize_transfer_service(payload.model_dump())
