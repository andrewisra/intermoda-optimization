from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routes import eta, optimizer, density, incidents

app = FastAPI(
    title='Intermodal AI System - DKI Jakarta',
    description='Prototype ETA, density, transfer optimization, dwell-time decision, incident-aware adjustment.',
    version='0.1.0',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(eta.router)
app.include_router(optimizer.router)
app.include_router(density.router)
app.include_router(incidents.router)


@app.get('/')
def health_check():
    return {'status': 'running', 'service': 'Intermodal AI System', 'docs': '/docs'}
