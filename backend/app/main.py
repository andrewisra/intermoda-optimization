from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes import predict, optimize, data, incidents

app = FastAPI(
    title="AI Transit Synchronizer API",
    description="AI-based ETA prediction, passenger density prediction, and rail-fixed intermodal optimization.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)
app.include_router(optimize.router)
app.include_router(data.router)
app.include_router(incidents.router)


@app.get("/")
def root():
    return {
        "service": "AI Transit Synchronizer",
        "status": "running",
        "principle": "Rail-based transport is treated as fixed schedule anchor; non-rail modes are optimized around it.",
    }
