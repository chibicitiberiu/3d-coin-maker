# Docker Configuration Guide

This project uses a unified Docker setup that eliminates duplication between development and production configurations while maintaining environment-specific optimizations.

## Architecture

### Unified Dockerfiles
- **Single Dockerfile per service** with build arguments for environment-specific behavior
- **backend/Dockerfile**: Handles both dev and prod with `ENVIRONMENT` build arg
- **frontend/Dockerfile**: Multi-stage build with environment selection

### Compose File Structure
- **docker-compose.yml**: Base configuration with shared settings
- **docker-compose.override.yml**: Development overrides (applied automatically)
- **docker-compose.prod.yml**: Production overrides
- **docker-compose.apscheduler.yml**: APScheduler mode (no Redis/Celery)

## Usage

### Just Commands (Recommended)

**Quick start:**
```bash
# Development mode (backend + frontend only)
just docker-dev

# Development with Celery
just docker-dev celery

# Development with APScheduler  
just docker-dev apscheduler

# Production mode
just docker-prod

# Production with Celery
just docker-prod celery
```

**Management commands:**
```bash
# View logs
just docker-logs dev celery backend    # Specific service logs
just docker-logs prod                  # All production logs

# Stop containers
just stop-docker dev celery
just stop-docker prod

# Restart services
just restart-docker dev celery backend

# Check status
just docker-status dev celery

# Test configuration
just test-docker-config prod celery

# Clean up
just clean-docker
```

### Direct Docker Compose (Alternative)

**Development:**
```bash
# Uses docker-compose.yml + docker-compose.override.yml automatically
docker compose up

# With Celery services
docker compose --profile celery up

# APScheduler mode (no Redis/Celery)
docker compose -f docker-compose.yml -f docker-compose.apscheduler.yml up
```

**Production:**
```bash
# Production mode (backend + frontend only)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up

# Production with Celery services
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile celery up

# Production APScheduler mode (no Redis/Celery)
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.apscheduler.yml up
```

## Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables:
- `ENVIRONMENT`: `development` or `production`
- `UID/GID`: Your user/group IDs for file permissions
- `USE_CELERY`: `true` or `false`
- `BACKEND_PORT`: Backend service port
- `VITE_DEV_SERVER_PORT`: Frontend dev server port

## Build Arguments

### Backend Dockerfile
- `ENVIRONMENT`: Controls dev vs prod optimizations
- `UID/GID`: User permissions for development
- `USE_CELERY`: Celery configuration

### Frontend Dockerfile
- `ENVIRONMENT`: Selects dev server vs nginx production build

## Service Profiles

Services are organized using Docker Compose profiles:
- **celery**: Redis, Celery worker, and Celery beat services
- Default: Backend and frontend only

## Configuration Files

The new layered environment configuration eliminates duplication:

**Base configuration (shared settings):**
- `config/backend.base.env`: Shared backend settings
- `config/frontend.base.env`: Shared frontend settings

**Environment-specific overrides:**
- `config/backend.development.env`: Development backend overrides
- `config/backend.production.env`: Production backend overrides  
- `config/frontend.development.env`: Development frontend overrides
- `config/frontend.production.env`: Production frontend overrides

Docker Compose automatically loads both base + environment-specific files, with the environment-specific file taking precedence for any conflicting settings.

## Migration from Old Setup

The new unified setup replaces these old files:

**Dockerfiles:**
- OLD `backend/Dockerfile.prod` -> NEW `backend/Dockerfile` (with build args)
- OLD `frontend/Dockerfile.dev` -> NEW `frontend/Dockerfile` (with build args)

**Compose files:**
- OLD `docker-compose.dev.yml` -> NEW `docker-compose.override.yml`
- OLD `docker-compose.dev.apscheduler.yml` -> NEW `docker-compose.apscheduler.yml`

**Environment files:**
- OLD `config/backend.env` + `config/backend.dev.env` -> NEW `config/backend.base.env` + `config/backend.{environment}.env`
- OLD `config/frontend.env` + `config/frontend.dev.env` -> NEW `config/frontend.base.env` + `config/frontend.{environment}.env`

**Scripts and wrappers:**
- OLD `dc-dev.sh` -> NEW `just docker-dev` / `just docker-prod`
- OLD `scripts/dev-all.sh` -> NEW `just docker-dev celery`
- OLD `scripts/dev-backend.sh` -> NEW `just docker-logs dev celery backend`
- OLD `scripts/prod-deploy.sh` -> NEW `just docker-prod celery`
- OLD `run-dev-desktop.sh` -> NEW `just run-desktop`

## Benefits

1. **Reduced Duplication**: 
   - Single Dockerfile per service instead of separate dev/prod files
   - Layered environment files eliminate ~70% of duplicate configuration
2. **Consistent Behavior**: Same base operations for dev and prod with environment-specific optimizations
3. **Flexible Deployment**: Easy switching between development, production, and APScheduler modes
4. **Maintainable**: Changes to base functionality only need to be made in one place
5. **Environment Inheritance**: Base settings are shared, only differences need to be specified per environment