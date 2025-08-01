# Docker Deployment Guide

This guide covers deploying 3D Coin Maker using Docker and Docker Compose for production environments.

## Prerequisites

- **Docker**: 20.10 or higher
- **Docker Compose**: 2.0 or higher
- **System Requirements**: 2GB+ RAM, 5GB+ storage
- **Domain** (optional): For SSL/HTTPS setup

## Quick Start

### 1. Clone and Configure

```bash
git clone https://github.com/yourusername/3d-coin-maker.git
cd 3d-coin-maker

# Copy environment files
cp config/backend.env.example config/backend.env
cp config/frontend.env.example config/frontend.env
```

### 2. Production Configuration

Edit `config/backend.env`:
```bash
# CRITICAL: Change these for production
DEBUG=0
SECRET_KEY=your-super-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Rate limiting for production
MAX_GENERATIONS_PER_HOUR=20

# Security settings
CORS_ALLOW_ALL_ORIGINS=0
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database and cache
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO
```

Edit `config/frontend.env`:
```bash
# API endpoint
VITE_API_BASE_URL=https://yourdomain.com/api

# Application settings  
PUBLIC_APP_NAME=3D Coin Maker
PUBLIC_APP_VERSION=1.0.0
```

### 3. Deploy

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 4. Verify Deployment

```bash
# Test backend API
curl http://localhost:8000/api/health/
# Should return: {"status": "ok", "timestamp": "..."}

# Test frontend
curl http://localhost:3000/
# Should return HTML content

# Test Redis
docker compose exec redis redis-cli ping
# Should return: PONG
```

## Production Docker Compose

### Full Production Stack (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - frontend_build:/var/www/frontend:ro
      - backend_static:/var/www/static:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  # Frontend build and serve
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    volumes:
      - frontend_build:/app/build
    env_file:
      - config/frontend.env
    restart: unless-stopped

  # Django backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    volumes:
      - backend_static:/app/static
      - temp_files:/tmp/coin_maker
    env_file:
      - config/backend.env
    environment:
      - DJANGO_SETTINGS_MODULE=coin_maker.settings_production
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery worker
  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: celery -A coin_maker worker -l info --concurrency=4
    volumes:
      - temp_files:/tmp/coin_maker
    env_file:
      - config/backend.env
    environment:
      - DJANGO_SETTINGS_MODULE=coin_maker.settings_production
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "celery", "-A", "coin_maker", "inspect", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Redis cache and message broker
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  frontend_build:
  backend_static:
  temp_files:
  redis_data:

networks:
  default:
    name: coin_maker_network
```

### Nginx Configuration (`nginx.conf`)

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    limit_req_zone $binary_remote_addr zone=upload:10m rate=5r/m;

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # File upload limits
        client_max_body_size 50M;

        # Frontend static files
        location / {
            root /var/www/frontend;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # Backend API
        location /api/ {
            # Rate limiting
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeout settings
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s; # Long timeout for STL generation
        }

        # Upload endpoint with stricter rate limiting
        location /api/upload/ {
            limit_req zone=upload burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Django static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Stop nginx temporarily
docker compose stop nginx

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to project
sudo mkdir -p ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ssl/
sudo chown -R $(whoami):$(whoami) ssl/

# Restart nginx
docker compose up -d nginx
```

### Using Custom SSL Certificates

```bash
# Create SSL directory
mkdir -p ssl/

# Copy your certificates
cp your-fullchain.pem ssl/fullchain.pem
cp your-private-key.pem ssl/privkey.pem

# Set correct permissions
chmod 600 ssl/privkey.pem
chmod 644 ssl/fullchain.pem
```

## Environment Variables Reference

### Backend Configuration

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `DEBUG` | 1 | 0 | Django debug mode |
| `SECRET_KEY` | dev-key | **CHANGE!** | Django secret key |
| `ALLOWED_HOSTS` | localhost,127.0.0.1 | yourdomain.com | Allowed hosts |
| `LOG_LEVEL` | DEBUG | INFO | Logging level |
| `CORS_ALLOW_ALL_ORIGINS` | 1 | 0 | CORS policy |
| `MAX_GENERATIONS_PER_HOUR` | 100 | 20 | Rate limiting |

### Security Settings (Production)

| Variable | Value | Description |
|----------|-------|-------------|
| `SECURE_BROWSER_XSS_FILTER` | 1 | XSS protection |
| `SECURE_CONTENT_TYPE_NOSNIFF` | 1 | Content type protection |
| `SECURE_SSL_REDIRECT` | 0/1 | Force HTTPS |
| `SESSION_COOKIE_SECURE` | 0/1 | Secure cookies |
| `CSRF_COOKIE_SECURE` | 0/1 | Secure CSRF cookies |

## Security Checklist

Before production deployment:

- [ ] Change `SECRET_KEY` to a secure random value
- [ ] Set proper `ALLOWED_HOSTS` 
- [ ] Configure SSL certificates (if using HTTPS)
- [ ] Review rate limiting settings
- [ ] Enable security headers
- [ ] Set up monitoring and logging
- [ ] Configure backups for persistent volumes
- [ ] Test with production data
- [ ] Disable debug mode (`DEBUG=0`)
- [ ] Configure proper CORS origins

## Production Settings

### Backend Production Settings (`backend/coin_maker/settings_production.py`)

```python
from .settings import *
import os

# Security
DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/app/data/db.sqlite3',
    }
}

# Static files
STATIC_ROOT = '/app/static/'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Celery
CELERY_TASK_ALWAYS_EAGER = False
CELERY_WORKER_CONCURRENCY = 4

# Rate limiting
RATE_LIMIT_ENABLED = True
MAX_GENERATIONS_PER_HOUR = int(os.getenv('MAX_GENERATIONS_PER_HOUR', 20))

# File cleanup
FILE_CLEANUP_ENABLED = True
FILE_CLEANUP_MAX_AGE = 1800  # 30 minutes
```

### Frontend Production Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile

COPY . .
RUN pnpm run build

FROM nginx:alpine AS production
COPY --from=builder /app/build /var/www/frontend
```

### Backend Production Dockerfile

```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "coin_maker.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check all services
docker compose ps

# Check service health
docker compose exec backend curl -f http://localhost:8000/api/health/
docker compose exec redis redis-cli ping
docker compose exec celery celery -A coin_maker inspect ping
```

### Log Monitoring

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f celery
docker compose logs -f nginx

# Monitor errors only
docker compose logs -f | grep ERROR
```

### Application Metrics

Monitor these key metrics for production:

- **API Health**: `GET /api/health/` endpoint response
- **Container Resource Usage**: CPU, memory, disk usage
- **API Response Times**: Average and P95 response times
- **Task Processing Times**: STL generation completion times
- **Redis Memory Usage**: Cache hit rates and memory consumption
- **File Storage Usage**: Temporary file cleanup effectiveness
- **Rate Limiting**: Requests blocked per IP

### Resource Monitoring

```bash
# Check resource usage
docker stats

# Check disk usage
docker system df

# Clean unused resources
docker system prune -f
```

### Backup and Restore

```bash
# Backup Redis data
docker compose exec redis redis-cli BGSAVE
docker cp $(docker compose ps -q redis):/data/dump.rdb ./backup-redis-$(date +%Y%m%d).rdb

# Backup application data
tar -czf backup-app-$(date +%Y%m%d).tar.gz config/ ssl/ docker-compose.yml

# Restore Redis data
docker compose stop redis
docker cp ./backup-redis-20240101.rdb $(docker compose ps -q redis):/data/dump.rdb
docker compose start redis
```

### Updates and Maintenance

#### Development Updates
```bash
# Pull latest code and restart
git pull
./dc-dev.sh recreate
```

#### Production Updates
```bash
# Update application
git pull origin main

# Rebuild and restart services
docker compose build --no-cache
docker compose up -d

# Update base images
docker compose pull
docker compose up -d

# Clean old images
docker image prune -f
```

## Performance Optimization

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  celery:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### Redis Optimization

```bash
# Add to docker-compose.yml redis service
command: >
  redis-server
  --appendonly yes
  --maxmemory 256mb
  --maxmemory-policy allkeys-lru
  --tcp-keepalive 60
  --timeout 300
```

## Troubleshooting

### Common Issues

**Container Won't Start**
```bash
# Check logs for errors
docker compose logs backend

# Check configuration
docker compose config

# Rebuild container
docker compose build --no-cache backend
```

**SSL Certificate Issues**
```bash
# Test certificate
openssl x509 -in ssl/fullchain.pem -text -noout

# Check nginx configuration
docker compose exec nginx nginx -t

# Reload nginx
docker compose exec nginx nginx -s reload
```

**Performance Issues**
```bash
# Check resource usage
docker stats

# Monitor slow queries
docker compose logs backend | grep "slow"

# Check Redis memory
docker compose exec redis redis-cli info memory
```

**File Upload Issues**
```bash
# Check file permissions
docker compose exec backend ls -la /tmp/coin_maker/

# Check nginx upload limit
docker compose logs nginx | grep "413"
```

For more troubleshooting tips, see the [troubleshooting guide](troubleshooting.md).