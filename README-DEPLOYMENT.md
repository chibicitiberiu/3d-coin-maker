# Coin Maker Deployment Guide

This guide explains how to deploy Coin Maker in both development and production environments.

## 🛠️ Development Environment

### Configuration Files

Development configuration is in `config/backend.dev.env`:
- **DEBUG=1** - Enable debug mode
- **Relaxed rate limits** - Higher limits for testing
- **Verbose logging** - DEBUG level logs
- **CORS_ALLOW_ALL=1** - Allow all origins for development

### Starting Development Environment

```bash
# Start all services (backend + frontend + redis + celery)
./scripts/dev-all.sh

# Or start just backend services
./scripts/dev-backend.sh

# Or use Docker Compose directly
docker compose -f docker-compose.dev.yml up
```

**Available Services:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- Redis: localhost:6379

### Development Features

- **Hot reloading** for both backend and frontend
- **Volume mounts** for live code changes
- **Debug logging** enabled
- **All dev dependencies** installed (pytest, ruff, pyright)
- **Source maps** and development builds

## 🚀 Production Environment

### Configuration Files

Production configuration is in `config/backend.env`:
- **DEBUG=0** - Disable debug mode
- **Strong security settings** - XSS protection, content type sniffing protection
- **Production rate limits** - Conservative limits
- **INFO level logging** - Production appropriate logging
- **CORS_ALLOW_ALL=0** - Restricted CORS origins

### Required Production Setup

1. **Update Secret Key**:
   ```bash
   # Generate a new secret key
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Update `SECRET_KEY` in `config/backend.env`

2. **Set Allowed Hosts**:
   ```bash
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

3. **Configure SSL (if needed)**:
   ```bash
   SECURE_SSL_REDIRECT=1
   SESSION_COOKIE_SECURE=1
   CSRF_COOKIE_SECURE=1
   ```

### Production Deployment

```bash
# Deploy to production
./scripts/prod-deploy.sh

# Or use Docker Compose directly
docker compose up -d --build
```

**Available Services:**
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000
- Redis: Internal network only

### Production Features

- **Gunicorn WSGI server** (3 workers)
- **Non-root user** for security
- **Health checks** configured
- **Persistent volumes** for data
- **Restart policies** for reliability
- **Optimized Redis** with memory limits
- **Static file serving** configured

## 📁 File Structure

```
config/
├── backend.dev.env      # Development backend config
├── backend.env          # Production backend config
├── frontend.dev.env     # Development frontend config
└── frontend.env         # Production frontend config

backend/
├── Dockerfile          # Development Dockerfile
└── Dockerfile.prod     # Production Dockerfile

docker-compose.dev.yml  # Development services
docker-compose.yml      # Production services

scripts/
├── dev-all.sh         # Start all dev services
├── dev-backend.sh     # Start backend dev services
└── prod-deploy.sh     # Production deployment
```

## 🔧 Environment Variables

### Backend Configuration

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `DEBUG` | 1 | 0 | Django debug mode |
| `SECRET_KEY` | dev-key | **CHANGE!** | Django secret key |
| `ALLOWED_HOSTS` | localhost,127.0.0.1 | yourdomain.com | Allowed hosts |
| `LOG_LEVEL` | DEBUG | INFO | Logging level |
| `CORS_ALLOW_ALL` | 1 | 0 | CORS policy |
| `MAX_GENERATIONS_PER_HOUR` | 100 | 20 | Rate limiting |

### Security Settings (Production)

| Variable | Value | Description |
|----------|-------|-------------|
| `SECURE_BROWSER_XSS_FILTER` | 1 | XSS protection |
| `SECURE_CONTENT_TYPE_NOSNIFF` | 1 | Content type protection |
| `SECURE_SSL_REDIRECT` | 0/1 | Force HTTPS |
| `SESSION_COOKIE_SECURE` | 0/1 | Secure cookies |

## 🚨 Security Checklist

Before production deployment:

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Set proper `ALLOWED_HOSTS` 
- [ ] Configure SSL certificates (if using HTTPS)
- [ ] Review rate limiting settings
- [ ] Enable security headers
- [ ] Set up monitoring and logging
- [ ] Configure backups for persistent volumes
- [ ] Test with production data

## 📊 Monitoring

### Health Checks

- **Backend**: `GET /api/health/`
- **Services**: OpenSCAD, Redis, Storage
- **Docker**: Built-in health checks

### Logs

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f celery
```

### Metrics

- Container resource usage
- API response times
- Task processing times
- Redis memory usage
- File storage usage

## 🔄 Updates and Maintenance

### Development Updates
```bash
# Pull latest code and restart
git pull
docker compose -f docker-compose.dev.yml up --build
```

### Production Updates
```bash
# Backup data first
docker compose exec backend python manage.py dumpdata > backup.json

# Deploy updates
./scripts/prod-deploy.sh
```

### Database Migrations
```bash
# Development
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate

# Production  
docker compose exec backend python manage.py migrate
```