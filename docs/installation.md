# Installation Guide

This guide covers installation of 3D Coin Maker for both development and production. The application includes a modern Just-based build system and supports multiple deployment modes.

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.11-3.12 (3.13+ not yet supported by PyInstaller)
- **Node.js**: 20 or higher  
- **Just**: Task runner (https://just.systems)
- **GLM**: Math library for HMM compilation
- **Redis**: 6.0 or higher (only required for Celery mode)
- **Memory**: 2GB+ RAM recommended
- **Storage**: 2GB+ free space (includes HMM compilation)

## Task Processing Modes

3D Coin Maker supports two different background task processing architectures:

### Celery Mode (Recommended for Production)
- **Requirements**: Redis server for task coordination
- **Architecture**: Distributed task queue with separate worker processes
- **Scalability**: Can scale horizontally across multiple servers
- **Use Cases**: Production web applications, multi-user environments

### APScheduler Mode (Simplified Setup)
- **Requirements**: None (no external dependencies)
- **Architecture**: In-process task scheduling using threads
- **Scalability**: Single-process, limited to one server
- **Use Cases**: Development, testing, simple deployments

Choose APScheduler mode if you want to avoid setting up Redis or prefer a simpler architecture.

### Installing Prerequisites

#### Ubuntu/Debian

**For Celery Mode (with Redis):**
```bash
# Update package list
sudo apt update

# Install Python, Node.js, and Redis
sudo apt install python3 python3-pip nodejs npm redis-server

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install pnpm
npm install -g pnpm
```

**For APScheduler Mode (no Redis):**
```bash
# Update package list
sudo apt update

# Install Python and Node.js (no Redis needed)
sudo apt install python3 python3-pip nodejs npm

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install pnpm
npm install -g pnpm
```

#### macOS (Homebrew)

**For Celery Mode (with Redis):**
```bash
# Install Python, Node.js, and Redis
brew install python@3 node redis

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install pnpm
npm install -g pnpm
```

**For APScheduler Mode (no Redis):**
```bash
# Install Python and Node.js (no Redis needed)
brew install python@3 node

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install pnpm
npm install -g pnpm
```

#### Windows

**For Celery Mode (with Redis):**
```powershell
# Install using Chocolatey
choco install python nodejs redis-64

# Install Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Install pnpm
npm install -g pnpm
```

**For APScheduler Mode (no Redis):**
```powershell
# Install using Chocolatey (no Redis needed)
choco install python nodejs

# Install Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Install pnpm
npm install -g pnpm
```

## Quick Start with Just

The easiest way to get started is using the Just build system:

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/3d-coin-maker.git
cd 3d-coin-maker
```

### 2. Install Just Task Runner

```bash
# Linux/macOS
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin

# Or via package manager:
# Ubuntu/Debian: apt install just
# macOS: brew install just
# Fedora: dnf install just
```

### 3. Quick Setup and Run

```bash
# Check system dependencies
just check-deps

# Complete development setup (installs deps, builds HMM)
just dev-setup

# Run desktop application
just run-desktop

# OR run with Docker
just run-docker
```

### 4. Available Commands

Use `just --list` to see all available commands or `just help` for detailed help:

```bash
# Development
just run-desktop [dev|prod]    # Run desktop app
just run-docker [dev|prod]     # Run with Docker containers
just dev-setup                 # Complete development setup

# Building
just build-frontend [mode]     # Build frontend (dev/prod/desktop)
just build-desktop [mode]      # Build complete desktop app
just build-appimage           # Create Linux AppImage package
just build-flatpak            # Create Linux Flatpak package

# Dependencies  
just build-hmm                # Build HMM library dependency
just install-deps             # Install all project dependencies

# Utilities
just clean                    # Clean all build artifacts
just format                   # Format code
just lint                     # Lint code
just test                     # Run tests
```

## Manual Installation Steps

If you prefer manual setup or need to customize the installation:

### 1. System Dependencies

Install the required system packages for your platform:

#### Ubuntu/Debian
```bash
# Install base dependencies
sudo apt update
sudo apt install python3 python3-pip nodejs npm git build-essential cmake make pkg-config

# Install GLM for HMM compilation
sudo apt install libglm-dev

# For Celery mode (optional)
sudo apt install redis-server

# Install Poetry and pnpm
curl -sSL https://install.python-poetry.org | python3 -
npm install -g pnpm
```

#### Fedora
```bash
# Install base dependencies
sudo dnf install python3 python3-pip nodejs npm git gcc-c++ cmake make pkgconfig

# Install GLM for HMM compilation
sudo dnf install glm-devel

# For Celery mode (optional)
sudo dnf install redis

# Install Poetry and pnpm
curl -sSL https://install.python-poetry.org | python3 -
npm install -g pnpm
```

#### macOS
```bash
# Install base dependencies
brew install python@3 node git cmake make pkg-config

# Install GLM for HMM compilation
brew install glm

# For Celery mode (optional)
brew install redis

# Install Poetry and pnpm
curl -sSL https://install.python-poetry.org | python3 -
npm install -g pnpm
```

### 2. Backend Setup

```bash
cd backend/

# Install Python dependencies
poetry install

# Copy environment configuration
cp ../config/backend.env.example ../config/backend.env

# Edit configuration (see Environment Configuration below)
nano ../config/backend.env

# Test backend installation
poetry run python -m uvicorn fastapi_main:app --host 127.0.0.1 --port 8000
```

### 3. Frontend Setup

```bash
cd ../frontend/

# Install Node.js dependencies
pnpm install

# Copy environment configuration
cp ../config/frontend.env.example ../config/frontend.env

# Edit configuration
nano ../config/frontend.env

# Build frontend for production
pnpm run build

# Test frontend (development mode)
pnpm run dev
```

### 4. HMM Dependency Setup

The application requires the HMM (Height Map Mesher) library for 3D mesh generation:

```bash
# This is automated with Just: just build-hmm
# Manual setup:

# Clone HMM library
mkdir -p build/external
git clone https://github.com/fogleman/hmm.git build/external/hmm

# Build HMM (requires GLM headers)
cd build/external/hmm
make
cd ../../..

# Create symlink for easy access
ln -sf build/external/hmm/hmm build/hmm
```

### 4. Redis Setup (Celery Mode Only)

**Skip this section if using APScheduler mode.**

#### Linux/macOS
```bash
# Start Redis server
redis-server

# Test Redis connection
redis-cli ping
# Should return: PONG
```

#### Windows
```powershell
# Start Redis server (as administrator)
redis-server

# Test connection
redis-cli ping
```

### 5. Start Services

#### Using Just (Recommended)

**Desktop Application (with GUI):**
```bash
# Development mode
just run-desktop dev

# Production mode  
just run-desktop prod
```

**Web Application (Docker):**
```bash
# Development mode
just run-docker dev

# Production mode
just run-docker prod

# Stop containers
just stop-docker dev
```

#### Manual Startup

Choose the appropriate startup method based on your selected mode:

**Celery Mode Startup:**

Terminal 1: Redis
```bash
redis-server
```

Terminal 2: FastAPI Backend
```bash
cd backend/
poetry run python -m uvicorn fastapi_main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 3: Celery Worker
```bash
cd backend/
poetry run celery -A celery_app worker -l info
```

Terminal 4: Frontend (Development)
```bash
cd frontend/
pnpm run dev
```

**APScheduler Mode Startup:**

Terminal 1: FastAPI Backend (with integrated task processing)
```bash
cd backend/
poetry run python -m uvicorn fastapi_main:app --host 0.0.0.0 --port 8000
```

Terminal 2: Frontend (Development)
```bash
cd frontend/
pnpm run dev
```

**Note**: In APScheduler mode, background tasks run within the FastAPI process, so no separate Redis or Celery worker is needed.

## Environment Configuration

### Backend Configuration (`config/backend.env`)

**Common Settings (both modes):**
```bash
# Basic Settings
DEBUG=1                                    # Set to 0 for production
SECRET_KEY=your-very-secure-secret-key-here  # Generate a secure key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite default)
DATABASE_URL=sqlite:///db.sqlite3

# Rate Limiting
MAX_GENERATIONS_PER_HOUR=100              # Higher limit for development

# File Storage
TEMP_DIR=/tmp/coin_maker                  # Temporary file storage
FILE_CLEANUP_INTERVAL=300                 # Cleanup every 5 minutes

# CORS Settings
CORS_ALLOW_ALL_ORIGINS=1                  # Set to 0 for production
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

**For Celery Mode (add these settings):**
```bash
# Task Queue Mode
USE_CELERY=true

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**For APScheduler Mode (add these settings):**
```bash
# Task Queue Mode
USE_CELERY=false

# No Redis configuration needed
```

### Frontend Configuration (`config/frontend.env`)

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api

# Application Settings
PUBLIC_APP_NAME=3D Coin Maker
PUBLIC_APP_VERSION=1.0.0

# Development Settings
VITE_DEV_MODE=1
```

## Desktop Application Packaging

### Linux AppImage

Create a portable Linux application:

```bash
# Build AppImage (requires Python 3.11-3.12)
just build-appimage

# The AppImage will be created in build/
./build/CoinMaker-x86_64.AppImage
```

**Requirements for AppImage building:**
- Python 3.11 or 3.12 (PyInstaller limitation)
- All system dependencies installed
- GLM development headers

### Linux Flatpak

Create a sandboxed Linux package for distribution via Flathub or direct installation:

```bash
# Build Flatpak package
just build-flatpak

# Install locally for testing
just install-flatpak

# Run the installed Flatpak
flatpak run io.github.coinmaker.CoinMaker

# Export as distributable bundle
just export-flatpak

# The Flatpak bundle will be created in build/
# Users can install with: flatpak install CoinMaker-x86_64.flatpak
```

**Requirements for Flatpak building:**
- flatpak-builder package installed
- Flatpak runtime (automatically installed if missing)
- All project dependencies (automatically handled by Flatpak)

**Flatpak advantages:**
- Sandboxed execution for security
- Automatic dependency management
- Cross-distribution compatibility
- Integrated with Linux desktop environments
- Easy distribution via Flathub

**Installing flatpak-builder:**
```bash
# Fedora/RHEL
sudo dnf install flatpak-builder

# Ubuntu/Debian  
sudo apt install flatpak-builder

# Arch Linux
sudo pacman -S flatpak-builder
```

### Development vs Production Builds

```bash
# Development build (with debug info)
just build-desktop dev

# Production build (optimized)
just build-desktop prod

# Desktop-specific build (optimized for desktop packaging)
just build-frontend desktop
```

## Production Configuration

### Backend Production Settings

```bash
# Security
DEBUG=0
SECRET_KEY=generate-a-secure-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# CORS Security
CORS_ALLOW_ALL_ORIGINS=0
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Rate Limiting
MAX_GENERATIONS_PER_HOUR=20

# Logging
LOG_LEVEL=INFO
```

### Frontend Production Build

```bash
cd frontend/

# Set production environment
echo "VITE_API_BASE_URL=https://yourdomain.com/api" > ../config/frontend.env

# Build for production
pnpm run build

# Serve with a web server (nginx, apache, etc.)
```

## System Service Setup

### Systemd Services (Linux)

#### Backend Service (`/etc/systemd/system/coin-maker-backend.service`)

```ini
[Unit]
Description=3D Coin Maker Backend
After=network.target redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/3d-coin-maker/backend
EnvironmentFile=/path/to/3d-coin-maker/config/backend.env
ExecStart=/path/to/poetry run gunicorn fastapi_main:app --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Celery Service (`/etc/systemd/system/coin-maker-celery.service`)

```ini
[Unit]
Description=3D Coin Maker Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/3d-coin-maker/backend
EnvironmentFile=/path/to/3d-coin-maker/config/backend.env
ExecStart=/path/to/poetry run celery -A celery_app worker -l info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable coin-maker-backend coin-maker-celery
sudo systemctl start coin-maker-backend coin-maker-celery

# Check status
sudo systemctl status coin-maker-backend
sudo systemctl status coin-maker-celery
```

## Web Server Configuration

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # Frontend static files
    location / {
        root /path/to/3d-coin-maker/frontend/build;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /path/to/3d-coin-maker/backend/static/;
    }
}
```

### Apache Configuration

```apache
<VirtualHost *:80>
    ServerName yourdomain.com
    DocumentRoot /path/to/3d-coin-maker/frontend/build
    
    # Frontend
    <Directory /path/to/3d-coin-maker/frontend/build>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        
        # SPA routing
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
    
    # Backend API proxy
    ProxyPreserveHost On
    ProxyPass /api/ http://127.0.0.1:8000/api/
    ProxyPassReverse /api/ http://127.0.0.1:8000/api/
</VirtualHost>
```

## Verification

### Test Installation

**Common Tests (both modes):**
```bash
# Test backend API
curl http://localhost:8000/api/health/

# Test frontend (if running dev server)
curl http://localhost:5173/
```

**Additional Tests for Celery Mode:**
```bash
# Test Redis connection
redis-cli ping

# Test Celery worker
cd backend/
poetry run celery -A celery_app inspect active
```

**Verify Task Processing Mode:**
```bash
# Check which mode is active
curl http://localhost:8000/api/health/ | grep -o '"queue_type":"[^"]*"'
# Should return: "queue_type":"celery" or "queue_type":"apscheduler"
```

### Health Checks

```bash
# Backend health
curl -f http://localhost:8000/api/health/ || echo "Backend unhealthy"

# Redis health
redis-cli ping | grep -q PONG || echo "Redis unhealthy"

# Celery health
cd backend/
poetry run celery -A celery_app inspect ping
```

## Troubleshooting

### Common Issues

**Just Not Found**
```bash
# Install Just task runner
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to ~/.local/bin

# Add to PATH if needed
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**HMM Build Failures**
```bash
# Check GLM headers
just check-deps

# Install GLM manually:
# Ubuntu/Debian: sudo apt install libglm-dev
# Fedora: sudo dnf install glm-devel
# macOS: brew install glm

# Force rebuild HMM
just clean
just build-hmm
```

**PyInstaller Python Version Issues**
```bash
# Check Python version
python3 --version

# PyInstaller requires Python 3.11-3.12
# Use pyenv to manage Python versions:
pyenv install 3.12.0
pyenv local 3.12.0

# Recreate Poetry environment
poetry env remove python
poetry env use python3.12
poetry install
```

**Python Version Issues**
```bash
# Check Python version
python3 --version

# Use specific Python version with Poetry
poetry env use python3.11
```

**Permission Issues**
```bash
# Fix file permissions
sudo chown -R www-data:www-data /path/to/3d-coin-maker
sudo chmod -R 755 /path/to/3d-coin-maker
```

**Redis Connection Issues**
```bash
# Check Redis status
sudo systemctl status redis
redis-cli ping

# Check Redis configuration
sudo nano /etc/redis/redis.conf
```

**Port Already in Use**
```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process if needed
sudo kill -9 <PID>
```

### Log Locations

- **Backend Logs**: Check Django console output or configure logging in settings
- **Celery Logs**: Console output or configure file logging
- **Redis Logs**: `/var/log/redis/redis-server.log` (Linux)
- **System Logs**: `journalctl -u coin-maker-backend` (systemd)

### Performance Tuning

**Backend Optimization**
```bash
# Use Gunicorn for production
poetry run gunicorn coin_maker.wsgi:application --workers 4 --bind 0.0.0.0:8000

# Optimize Celery
poetry run celery -A celery_app worker -l info --concurrency=4
```

**Redis Optimization**
```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Key settings:
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
```

For additional help, see the [troubleshooting guide](troubleshooting.md) or open an issue on GitHub.