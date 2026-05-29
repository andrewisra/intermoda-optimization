from __future__ import annotations

from fastapi import APIRouter
from backend.app.models.schemas import TransferRequest, SpeedAdjustmentRequest
from src.simulator.transfer_simulator import simulate_transfer, simulate_all_transfer_nodes
from src.optimizer.speed_adjustment import recommend_speed_adjustment

router = APIRouter(prefix='/optimizer', tags=['Optimizer'])


@router.post('/transfer')
def optimize_transfer(req: TransferRequest):
    return simulate_transfer(req.from_stop_id, req.to_stop_id, req.current_time, req.first_mode_eta_minutes, req.target_route_id, req.load_factor)


@router.get('/simulate-all')
def simulate_all(current_time: str):
    df = simulate_all_transfer_nodes(current_time)
    return df.to_dict(orient='records')


@router.post('/speed')
def speed_adjustment(req: SpeedAdjustmentRequest):
    return recommend_speed_adjustment(req.current_speed_kmh, req.current_eta_minutes, req.target_arrival_in_minutes)
