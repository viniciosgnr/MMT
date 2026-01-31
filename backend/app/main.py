from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import equipment, calibration, chemical, maintenance, failures, alerts, sync, planning, export, history
from .database import engine, Base

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Seed sample data
from .seed import seed_data
seed_data()

app = FastAPI(title="MMT API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(equipment.router)
app.include_router(calibration.router)
app.include_router(chemical.router)
app.include_router(maintenance.router)
app.include_router(failures.router)
app.include_router(alerts.router)
app.include_router(sync.router)
app.include_router(planning.router)
app.include_router(export.router)
app.include_router(history.router)

@app.get("/")
def read_root():
    return {"message": "MMT API Ready - Phase 3"}

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.3.0"}
