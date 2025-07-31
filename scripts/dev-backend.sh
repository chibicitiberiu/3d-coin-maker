#!/bin/bash

# Start Django development server with Docker Compose
echo "Starting Django development server with Docker Compose..."
docker compose -f docker-compose.dev.yml up backend redis celery celery-beat