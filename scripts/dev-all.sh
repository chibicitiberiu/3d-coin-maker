#!/bin/bash

# Start all development services with Docker Compose
echo "Starting all development services with Docker Compose..."
echo "Backend will be available on http://localhost:8000"
echo "Frontend will be available on http://localhost:5173"
echo "Press Ctrl+C to stop all services"

docker compose -f docker-compose.dev.yml build
docker compose -f docker-compose.dev.yml up -d
