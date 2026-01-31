#!/bin/bash
source backend/venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
