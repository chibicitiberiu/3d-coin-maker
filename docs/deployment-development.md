# Development Setup Guide

This guide covers setting up 3D Coin Maker for development with hot reloading, debug logging, and testing both task processing architectures.

## Development Environment Overview

The development environment provides:

- **Hot Reloading**: Code changes automatically restart the Django dev server and Vite frontend
- **Debug Logging**: Detailed logging output for troubleshooting task processing and API calls
- **Relaxed Rate Limits**: Higher generation limits for testing (100/hour vs 20/hour in production)
- **Both Task Modes**: Easy switching between Celery and APScheduler implementations

## Task Processing Architecture Comparison

3D Coin Maker implements a unified task queue abstraction supporting two different background processing architectures:

### Celery Mode (Production Architecture)
- **Task Processing**: Distributed task queue with separate worker processes
- **Dependencies**: Requires Redis (or other message broker) for task coordination
- **Persistence**: Task state persisted in Redis, survives application restarts
- **Scaling**: Multi-process, can scale horizontally across multiple servers
- **Monitoring**: Rich ecosystem of monitoring tools (Flower, Celery Beat, etc.)
- **Container Count**: 4+ containers (Django, frontend, Redis, Celery workers)
- **Services**: Django backend, SvelteKit frontend, Redis, Celery worker
- **Command**: `./dc-dev.sh run`

### APScheduler Mode (Simplified Architecture)
- **Task Processing**: In-process scheduler using Python's `concurrent.futures.ThreadPoolExecutor`
- **Dependencies**: None - all processing happens within the Django application process
- **Persistence**: Task state stored in memory (non-persistent across restarts)
- **Scaling**: Single-process, multi-threaded (vertical scaling only)
- **Monitoring**: Standard Django logging, simpler debugging
- **Container Count**: 2 containers (Django with integrated scheduler, frontend)
- **Services**: Django backend, SvelteKit frontend (no Redis/Celery needed)
- **Command**: `./dc-dev.sh --mode apscheduler run`

### Key Differences Summary

| Feature | Celery Mode | APScheduler Mode |
|---------|-------------|------------------|
| Task Processing | Distributed (Redis + Workers) | In-process (Threads) |
| External Dependencies | Redis server required | None |
| Scalability | Horizontal scaling | Single instance |
| Use Case | Multi-user web hosting | Single-user desktop |
| Container Count | 4+ containers | 2 containers |
| Task Persistence | Survives restarts | Lost on restart |
| Debugging Complexity | Multiple log sources | Single log source |
| Resource Requirements | Higher (Redis + workers) | Lower (single process) |

The APScheduler mode is primarily intended for development and testing. It provides a simpler architecture for understanding task flow and debugging, and could potentially be used for future desktop application implementations.

## Why Test Both Modes?

**Testing both architectures ensures:**
- Code changes work correctly with both task processing implementations
- Task functions are properly abstracted from the underlying queue system
- Progress callbacks and error handling work consistently
- Performance characteristics are understood for both approaches

---

## Prerequisites

- **Docker & Docker Compose**: 20.10+ (recommended)
- **OR** Python 3.11+ and Node.js 20+ (manual setup)
- **Git**: For version control
- **System Requirements**: 2GB+ RAM, 2GB+ storage

## Quick Start (Docker Development)

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/3d-coin-maker.git
cd 3d-coin-maker

# Copy development environment files
cp config/backend.dev.env config/backend.env
cp config/frontend.dev.env config/frontend.env
```

### 2. Start Development Environment

Choose your deployment mode for testing:

```bash
# Start in Celery mode (default - for web deployment testing)
./dc-dev.sh run

# Start in APScheduler mode (for desktop deployment testing)
./dc-dev.sh --mode apscheduler run

# Or start specific services (Celery mode)
./dc-dev.sh run backend redis celery
./dc-dev.sh run frontend-dev
```

### 3. Access Application

- **Frontend**: http://localhost:5173 (Vite dev server with HMR)
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/
- **Health Check**: http://localhost:8000/api/health/

## Development Wrapper Script

The `dc-dev.sh` script provides convenient shortcuts for development:

### Basic Usage

```bash
# Start all services in background
./dc-dev.sh run

# Start specific services only
./dc-dev.sh run backend redis celery
./dc-dev.sh run frontend-dev

# Restart after code changes
./dc-dev.sh restart backend
./dc-dev.sh restart frontend-dev

# Full clean rebuild (useful after dependency changes)
./dc-dev.sh recreate

# View logs
./dc-dev.sh logs -f backend
./dc-dev.sh logs -f frontend-dev

# Check service status
./dc-dev.sh ps

# Stop all services
./dc-dev.sh down

# Execute commands in containers
./dc-dev.sh exec backend python manage.py shell
./dc-dev.sh exec backend python manage.py migrate
```

## Task Queue Modes

The development environment supports two task processing modes for testing different deployment scenarios:

### Celery Mode (Default - Web Deployment)

**Use Case**: Testing web deployment with distributed task processing
**Services**: `backend`, `frontend-dev`, `redis`, `celery-dev`
**Start Command**: `./dc-dev.sh run`

```bash
# Check health endpoint
curl http://localhost:8000/api/health/ | jq '.services.task_queue.stats.queue_type'
# Returns: "celery"

# Services running
./dc-dev.sh ps
# Shows: backend, frontend-dev, redis, celery worker
```

### APScheduler Mode (Desktop Deployment)

**Use Case**: Testing desktop deployment with in-process task processing
**Services**: `backend`, `frontend-dev` (no Redis or Celery needed)
**Start Command**: `./dc-dev.sh --mode apscheduler run`

```bash
# Check health endpoint
curl http://localhost:8000/api/health/ | jq '.services.task_queue.stats.queue_type'
# Returns: "apscheduler"

# Services running
./dc-dev.sh ps
# Shows: backend, frontend-dev (no Redis/Celery containers)
```

### Switching Between Modes

```bash
# Stop current mode
./dc-dev.sh down

# Start in different mode
./dc-dev.sh --mode celery run      # Web deployment mode
./dc-dev.sh --mode apscheduler run # Desktop deployment mode
```

### Available Services

**Celery Mode Services:**
- **`backend-dev`**: Django development server with auto-reload
- **`frontend-dev`**: SvelteKit dev server with HMR
- **`redis`**: Redis cache and message broker
- **`celery-dev`**: Celery worker with auto-reload

**APScheduler Mode Services:**
- **`backend-dev`**: Django with APScheduler (no external dependencies)
- **`frontend-dev`**: SvelteKit dev server with HMR

## Development Docker Compose

### Configuration (`docker-compose.dev.yml`)

```yaml
version: '3.8'

services:
  # Backend development server
  backend-dev:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - temp_files:/tmp/coin_maker
    env_file:
      - config/backend.env
    environment:
      - DJANGO_SETTINGS_MODULE=coin_maker.settings
      - PYTHONPATH=/app
    depends_on:
      - redis
    command: python manage.py runserver 0.0.0.0:8000
    restart: unless-stopped

  # Frontend development server
  frontend-dev:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    env_file:
      - config/frontend.env
    command: npm run dev -- --host 0.0.0.0
    restart: unless-stopped

  # Celery worker for background tasks
  celery-dev:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    volumes:
      - ./backend:/app
      - temp_files:/tmp/coin_maker
    env_file:
      - config/backend.env
    environment:
      - DJANGO_SETTINGS_MODULE=coin_maker.settings
      - PYTHONPATH=/app
    depends_on:
      - redis
    command: celery -A coin_maker worker -l debug --reload
    restart: unless-stopped

  # Redis for caching and message broker
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_dev_data:/data
    restart: unless-stopped

volumes:
  temp_files:
  redis_dev_data:

networks:
  default:
    name: coin_maker_dev_network
```

## Manual Development Setup

### Backend Development

```bash
cd backend/

# Install dependencies
poetry install

# Copy development environment
cp ../config/backend.dev.env ../config/backend.env

# Run migrations
poetry run python manage.py migrate

# Start development server
poetry run python manage.py runserver

# In another terminal: Start Celery worker
poetry run celery -A coin_maker worker -l debug
```

### Frontend Development

```bash
cd frontend/

# Install dependencies
pnpm install

# Copy development environment
cp ../config/frontend.dev.env ../config/frontend.env

# Start development server
pnpm run dev
```

### Redis Setup

```bash
# Install and start Redis
# Ubuntu/Debian:
sudo apt install redis-server
sudo systemctl start redis-server

# macOS:
brew install redis
brew services start redis

# Windows:
# Download and install Redis from official website
```

## Development Configuration

### Backend Development Settings (`config/backend.dev.env`)

```bash
# Debug settings
DEBUG=1
LOG_LEVEL=DEBUG

# Security (relaxed for development)
SECRET_KEY=dev-secret-key-not-for-production
ALLOWED_HOSTS=localhost,127.0.0.1,backend-dev

# CORS (allow frontend dev server)
CORS_ALLOW_ALL_ORIGINS=1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Database
DATABASE_URL=sqlite:///db.sqlite3

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Rate limiting (relaxed for development)
MAX_GENERATIONS_PER_HOUR=100
RATE_LIMIT_ENABLED=0

# File storage
TEMP_DIR=/tmp/coin_maker
FILE_CLEANUP_ENABLED=1
FILE_CLEANUP_INTERVAL=300
FILE_CLEANUP_MAX_AGE=3600

# Development features
DJANGO_DEVELOPMENT=1
CELERY_TASK_ALWAYS_EAGER=0
```

### Frontend Development Settings (`config/frontend.dev.env`)

```bash
# API endpoint
VITE_API_BASE_URL=http://localhost:8000/api

# Development settings
VITE_DEV_MODE=1
VITE_DEBUG=1

# Application settings
PUBLIC_APP_NAME=3D Coin Maker (Dev)
PUBLIC_APP_VERSION=dev

# Hot module replacement
VITE_HMR=1
```

## Development Workflows

### Code Changes Workflow

```bash
# Backend changes (Python/Django)
# Changes are automatically reloaded by Django dev server
# If you change dependencies:
./dc-dev.sh restart backend-dev

# Frontend changes (TypeScript/Svelte)
# Changes are automatically reloaded by Vite HMR
# If you change dependencies:
cd frontend/ && pnpm install
./dc-dev.sh restart frontend-dev

# Environment changes
./dc-dev.sh restart backend-dev frontend-dev
```

### Application Management

```bash
# Access Django shell for debugging
./dc-dev.sh exec backend-dev python manage.py shell

# Check Django configuration
./dc-dev.sh exec backend-dev python manage.py check

# Or manually:
cd backend/
poetry run python manage.py shell
poetry run python manage.py check
```

### Testing Workflow

```bash
# Run backend tests
./dc-dev.sh exec backend-dev python -m pytest

# Run frontend type checking
./dc-dev.sh exec frontend-dev npm run check

# Run linting
cd backend/
poetry run ruff check .
poetry run pyright

cd frontend/
pnpm run check
```

### Debugging

#### Backend Debugging

```bash
# View Django logs
./dc-dev.sh logs -f backend-dev

# Access Django shell
./dc-dev.sh exec backend-dev python manage.py shell

# Check Celery tasks
./dc-dev.sh exec backend-dev python manage.py shell
# In shell:
from apps.processing.tasks import *
from celery import current_app
print(current_app.control.inspect().active())
```

#### Frontend Debugging

```bash
# View frontend logs
./dc-dev.sh logs -f frontend-dev

# Check build process
./dc-dev.sh exec frontend-dev npm run build

# Inspect bundle
./dc-dev.sh exec frontend-dev npm run preview
```

#### Redis Debugging

```bash
# Connect to Redis
./dc-dev.sh exec redis redis-cli

# Check Redis info
./dc-dev.sh exec redis redis-cli info

# Monitor Redis commands
./dc-dev.sh exec redis redis-cli monitor
```

## IDE Integration

### VS Code Setup

#### Recommended Extensions

Create `.vscode/extensions.json`:
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.black-formatter",
    "svelte.svelte-vscode",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

#### Workspace Settings

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./backend/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "typescript.preferences.importModuleSpecifier": "relative",
  "svelte.enable-ts-plugin": true,
  "files.associations": {
    "*.svelte": "svelte"
  },
  "emmet.includeLanguages": {
    "svelte": "html"
  }
}
```

#### Debug Configuration

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Django Debug",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/backend/manage.py",
      "args": ["runserver", "--noreload"],
      "django": true,
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "DJANGO_SETTINGS_MODULE": "coin_maker.settings"
      }
    }
  ]
}
```

### PyCharm Setup

1. **Open Project**: Open the `backend/` directory as the project root
2. **Python Interpreter**: Set to Poetry virtual environment
3. **Django Support**: Enable Django support in settings
   - Django project root: `backend/`
   - Settings: `coin_maker/settings.py`
   - Manage script: `manage.py`

## Performance Optimization for Development

### Docker Performance

```bash
# Use Docker Desktop with proper resource allocation
# Minimum: 4GB RAM, 2 CPU cores

# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

# Use bind mounts for better performance on macOS/Windows
# (Already configured in docker-compose.dev.yml)
```

### Frontend Performance

```bash
# Optimize Vite development server
# Add to frontend/vite.config.ts:
export default defineConfig({
  server: {
    hmr: {
      overlay: false  # Disable error overlay if needed
    },
    watch: {
      usePolling: false  # Better performance on Docker
    }
  }
})
```

### Backend Performance

```bash
# Use auto-reload only for changed files
# Already configured in Django dev server

# Optimize Celery for development
# Add to settings:
CELERY_TASK_ALWAYS_EAGER = False  # Use actual queue
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Reduce prefetch
```

## Troubleshooting

### Common Development Issues

**Port Already in Use**
```bash
# Find process using port
lsof -i :8000
lsof -i :5173

# Kill process or change port
./dc-dev.sh down
```

**File Permission Issues (Linux/macOS)**
```bash
# Fix file permissions
sudo chown -R $(whoami):$(whoami) .
chmod -R 755 .
```

**Node Modules Issues**
```bash
# Clear node_modules and reinstall
cd frontend/
rm -rf node_modules/ package-lock.json
pnpm install

# Or in Docker
./dc-dev.sh exec frontend-dev rm -rf node_modules/
./dc-dev.sh restart frontend-dev
```

**Python Dependencies Issues**
```bash
# Rebuild Python environment
cd backend/
poetry install --sync

# Or in Docker
./dc-dev.sh build --no-cache backend-dev
./dc-dev.sh restart backend-dev
```

**Redis Connection Issues**
```bash
# Check Redis status
./dc-dev.sh exec redis redis-cli ping

# Restart Redis
./dc-dev.sh restart redis

# Check Redis logs
./dc-dev.sh logs redis
```

### Development Performance Issues

**Slow Hot Reloading**
```bash
# Reduce file watching
# Add to .gitignore:
**/__pycache__/
**/node_modules/
**/.venv/
**/temp/

# Exclude from Docker volumes:
# Use .dockerignore files
```

**High Memory Usage**
```bash
# Monitor Docker resource usage
docker stats

# Limit container resources in docker-compose.dev.yml:
deploy:
  resources:
    limits:
      memory: 1G
```

For additional help with development setup, see the [troubleshooting guide](troubleshooting.md) or the main [README.md](../README.md).