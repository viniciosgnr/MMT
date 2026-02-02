#!/bin/bash

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed on this machine."
    echo "Please install Docker Desktop or Docker Engine first."
    exit 1
fi

echo "Starting MMT Application..."
echo "Building and launching containers..."

# Build and start in detached mode
docker compose up -d --build

echo ""
echo "============================================="
echo "Application started successfully!"
echo "============================================="
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000/docs"
echo "============================================="
echo "To stop the application, run: docker compose down"
