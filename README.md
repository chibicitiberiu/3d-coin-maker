# 3D Coin Maker

**Generate 3D printable coin STL files from images with customizable relief depth, size, and thickness parameters.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 20+](https://img.shields.io/badge/node-20+-green.svg)](https://nodejs.org/)

## Overview

3D Coin Maker is a self-hostable web application that transforms 2D images into 3D printable coins. Upload any image, adjust processing parameters, customize coin dimensions, and download ready-to-print STL files.

### Key Features

- **Image Processing**: Real-time brightness, contrast, gamma, and inversion adjustments
- **3D Preview**: Interactive Three.js viewer with STL visualization
- **Customizable Coins**: Adjustable diameter, thickness, and relief depth
- **High Performance**: HMM + Manifold3D backend for fast STL generation (100x faster than OpenSCAD)
- **Self-Hostable**: No external dependencies, run entirely on your infrastructure
- **Open Source**: AGPL v3 licensed for maximum transparency

### Screenshots

<!-- TODO: Add screenshots -->
*Screenshots will be added here showing:*
- *Main interface with image upload and processing controls*
- *Three-tab workflow: Original → Preprocessed → 3D Preview*  
- *STL viewer with interactive controls*
- *Coin parameter customization panel*

## Architecture

### Frontend (SvelteKit + TypeScript)
- **Framework**: SvelteKit 5.0 with TypeScript
- **3D Rendering**: Three.js STL viewer with interactive controls
- **Image Processing**: Photon WASM + Canvas fallback for real-time adjustments
- **UI**: PicoCSS framework with responsive two-panel layout
- **State Management**: Svelte stores with reactive updates

### Backend (FastAPI)
- **Framework**: FastAPI with Pydantic validation
- **Architecture**: Clean architecture with dependency injection
- **Task Processing**: Unified task queue abstraction (Celery + Redis for production, APScheduler for development)
- **3D Engine**: HMM + Manifold3D for high-performance mesh generation
- **Storage**: Temporary filesystem with automatic cleanup

### Task Queue Architecture
- **Unified Interface**: Abstract task queue supporting multiple implementations
- **Celery Mode**: Distributed processing with Redis for production deployment
- **APScheduler Mode**: In-process scheduling for development and testing
- **Dynamic Switching**: Environment-based mode selection (`USE_CELERY`)
- **Progress Reporting**: Real-time task progress updates in both modes

### Infrastructure
- **Containerization**: Docker + Docker Compose with deployment profiles
- **Rate Limiting**: Configurable per-IP limits (default: 20/hour)
- **Health Checks**: Built-in monitoring for all services
- **Security**: Input validation, CORS configuration, process isolation

## Installation

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** Python 3.11+ and Node.js 20+ (for local development)

### Quick Start (Docker)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/3d-coin-maker.git
   cd 3d-coin-maker
   ```

2. **Configure environment**
   ```bash
   cp config/backend.env.example config/backend.env
   cp config/frontend.env.example config/frontend.env
   # Edit configuration files as needed
   ```

3. **Start the application**
   ```bash
   docker compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - Health Check: http://localhost:8000/api/health/

### Manual Installation

See [docs/installation.md](docs/installation.md) for detailed manual setup instructions.

## Development Setup

### Prerequisites

- Python 3.11+ with Poetry
- Node.js 20+ with pnpm
- Redis server (or Docker)

### Backend Setup

```bash
cd backend/
poetry install
```

### Frontend Setup

```bash
cd frontend/
pnpm install
```

### Development Scripts

The development wrapper script supports both deployment modes:

```bash
# Start all services in Celery mode (default - for web deployment)
./dc-dev.sh run

# Start all services in APScheduler mode (for desktop deployment)
./dc-dev.sh --mode apscheduler run

# Start individual services (Celery mode)
./dc-dev.sh run backend redis celery
./dc-dev.sh run frontend-dev

# Monitor logs
./dc-dev.sh logs -f backend
./dc-dev.sh logs -f frontend-dev

# Restart after changes
./dc-dev.sh restart backend

# Rebuild and restart (useful for dependency changes)
./dc-dev.sh recreate backend
```

### Manual Development

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend
cd backend/
poetry run python -m uvicorn fastapi_main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3: Celery
cd backend/
poetry run celery -A celery_app worker -l info

# Terminal 4: Frontend
cd frontend/
pnpm run dev
```

## Deployment

3D Coin Maker can be deployed in production using Docker:

- **Production Deployment**: Celery + Redis for distributed task processing → [Docker Deployment Guide](docs/deployment-docker.md)
- **Development**: Test both Celery and APScheduler modes → [Development Guide](docs/deployment-development.md)

The application supports both Celery (distributed) and APScheduler (in-process) task processing. Currently, production deployment uses Celery mode, while APScheduler mode is available for development and testing.

### Environment Configuration

Key environment variables:

```bash
# Backend Configuration
DEBUG=0                           # Production: 0, Development: 1
SECRET_KEY=your-secret-key-here   # CHANGE FOR PRODUCTION
MAX_GENERATIONS_PER_HOUR=20      # Rate limiting

# Task Queue Configuration
USE_CELERY=true                   # true = Celery mode, false = APScheduler mode
CELERY_BROKER_URL=redis://redis:6379/0  # Only required for Celery mode

# Frontend Configuration  
VITE_API_BASE_URL=http://localhost:8000/api
PUBLIC_APP_NAME=3D Coin Maker
```

## API Reference

### Core Endpoints

- `POST /api/upload/` - Upload image, returns generation ID
- `POST /api/process/` - Process image with parameters
- `POST /api/generate/` - Generate STL with coin settings
- `GET /api/status/{id}/` - Check processing status
- `GET /api/download/{id}/stl` - Download generated STL
- `GET /api/preview/{id}` - Get processed heightmap image
- `GET /api/health/` - Service health check

### Workflow

1. **Upload**: POST image to `/api/upload/`
2. **Process**: Send processing parameters to `/api/process/`
3. **Generate**: Submit coin parameters to `/api/generate/`
4. **Monitor**: Poll `/api/status/{id}/` for completion
5. **Download**: Retrieve STL from `/api/download/{id}/stl`

## Project Structure

```
3d-coin-maker/
├── frontend/                 # SvelteKit frontend application
│   ├── src/
│   │   ├── routes/          # Page routes and layouts
│   │   ├── lib/             # Reusable components and services
│   │   │   ├── components/  # UI components
│   │   │   ├── services/    # Business logic services
│   │   │   └── stores/      # State management
│   │   └── static/          # Static assets
│   ├── Dockerfile
│   └── package.json
├── backend/                 # FastAPI backend application
│   ├── fastapi_main.py     # FastAPI application entry point
│   ├── fastapi_models.py   # Pydantic models
│   ├── fastapi_settings.py # Application settings
│   ├── celery_app.py       # Celery task definitions
│   ├── core/               # Clean architecture core
│   │   ├── interfaces/     # Abstract interfaces
│   │   ├── services/       # Business logic implementation
│   │   └── containers/     # Dependency injection
│   ├── Dockerfile.prod
│   └── pyproject.toml
├── config/                 # Environment configuration files
├── docs/                   # Documentation
├── scripts/               # Deployment and utility scripts
├── docker-compose.yml     # Production Docker configuration
├── docker-compose.dev.yml # Development Docker configuration
└── LICENSE                # AGPL v3 license
```

## Development

### Code Quality

```bash
# Backend linting and type checking
cd backend/
poetry run ruff check .
poetry run pyright

# Frontend type checking
cd frontend/
pnpm run check
```

### Testing

```bash
# Backend tests
cd backend/
poetry run pytest

# Integration tests
poetry run python -m pytest tests/test_integration.py
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the existing code style
4. Add tests for new functionality
5. Run the test suite and ensure all checks pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Performance

### Typical Performance Characteristics

- **Image Processing**: Sub-second for 4K images
- **STL Generation**: <30 seconds for standard coins
- **Memory Usage**: <512MB per generation
- **Concurrent Users**: 10+ simultaneous generations supported

### Optimization Tips

- Use SSD storage for temporary files
- Allocate 2GB+ RAM for production deployments  
- Configure Redis persistence for task queue reliability
- Enable file cleanup to prevent disk space issues

## Security

### Built-in Security Features

- Input validation on all file uploads
- Rate limiting per IP address (configurable)
- Process isolation for 3D generation
- Temporary file storage with automatic cleanup
- CORS configuration for API access
- No persistent user data storage

### Security Recommendations

- Change `SECRET_KEY` in production
- Use HTTPS in production environments
- Configure firewall rules for Docker containers
- Regular security updates for dependencies
- Monitor rate limiting logs for abuse

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

**Key Points:**
- **Free to use, modify, and distribute**
- **Source code must remain open**
- **Network copyleft**: Web service modifications must be shared
- **Commercial use allowed** under AGPL terms

See [LICENSE](LICENSE) for the full license text.

## Support

### Documentation
- [Installation Guide](docs/installation.md)
- [Deployment Options](docs/deployment-docker.md)
- [API Documentation](docs/api.md)
- [Development Setup](docs/development.md)

### Community
- **Issues**: [GitHub Issues](https://github.com/yourusername/3d-coin-maker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/3d-coin-maker/discussions)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)

### Troubleshooting

**Common Issues:**
- **STL Generation Fails**: Check Celery worker logs and ensure HMM dependencies are installed
- **Image Upload Issues**: Verify file size limits and supported formats
- **Performance Problems**: Monitor Redis memory usage and temporary file cleanup

**Getting Help:**
1. Check the [documentation](docs/)
2. Search [existing issues](https://github.com/yourusername/3d-coin-maker/issues)
3. Create a new issue with detailed reproduction steps
