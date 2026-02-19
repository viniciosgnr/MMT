from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from .routers import equipment, calibration, chemical, maintenance, failures, alerts, sync, planning, export, history, configuration
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
app.include_router(history.router)
app.include_router(configuration.router)
from .routers import audit_simulation
app.include_router(audit_simulation.router)

# Serve uploaded reports as static files
import os
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(os.path.join(uploads_dir, "reports"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/")
def read_root():
    return {"message": "MMT API Ready - Phase 3"}

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.3.0"}
