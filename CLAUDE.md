# Coin Maker - AI Agent Briefing

## Project Overview

**Coin Maker** is a self-hostable web application that generates 3D printable coin STL files from user-uploaded images. It features a modern SvelteKit frontend with real-time image processing and a Django REST API backend with background task processing.

**Current Status**: Stage 1 MVP - 95% complete, fully functional with frontend-backend integration

## Architecture

### Frontend (SvelteKit + TypeScript)
- **Location**: `frontend/`
- **Framework**: SvelteKit 5.0 with TypeScript
- **Styling**: PicoCSS framework
- **Key Features**:
  - Responsive two-panel layout (controls left, viewer right)
  - Client-side image processing with Photon WASM + Canvas fallback
  - Three.js STL viewer with interactive controls
  - Real-time parameter adjustments
  - Three-tab interface: Original → Preprocessed → Final Result

### Backend (Django + DRF)
- **Location**: `backend/`
- **Framework**: Django 4.2 + Django REST Framework
- **Architecture**: Clean architecture with dependency injection
- **Key Features**:
  - RESTful API endpoints for image upload/processing/STL generation
  - Celery task queue for background processing
  - Rate limiting (20 generations/hour per IP)
  - Temporary file storage with automatic cleanup
  - HMM + Manifold3D integration for high-performance STL generation

### Infrastructure
- **Container Orchestration**: Docker Compose
- **Task Queue**: Redis + Celery
- **Storage**: Temporary filesystem (no database)
- **Deployment**: Production-ready with health checks, logging, monitoring

## Key Technologies

### Frontend Stack
- **SvelteKit 5.0** - Modern reactive framework
- **TypeScript** - Type safety
- **Three.js** - 3D rendering for STL viewer
- **Photon WASM** - High-performance image processing
- **PicoCSS** - Lightweight CSS framework
- **Lucide Svelte** - Icon library

### Backend Stack
- **Django 4.2 + DRF** - Web framework and API
- **Celery 5.3** - Background task processing
- **Redis 7** - Cache and message broker
- **Pillow** - Image processing
- **HMM + Manifold3D** - High-performance 3D model generation (100x faster than OpenSCAD)
- **Trimesh** - 3D geometry processing

### Development Tools
- **Poetry** - Python dependency management
- **pnpm** - Node.js package manager
- **Ruff + Pyright** - Python linting/type checking
- **Docker** - Containerization

## Project Structure

```
/
├── frontend/                 # SvelteKit frontend
│   ├── src/
│   │   ├── routes/          # Page routes
│   │   │   ├── +layout.svelte
│   │   │   ├── +page.svelte  # Main app (1,982 lines - needs refactoring)
│   │   │   └── about/
│   │   └── lib/             # Reusable components
│   │       ├── STLViewer.svelte
│   │       ├── api.ts       # API client
│   │       └── imageProcessor.ts
│   ├── package.json
│   └── Dockerfile
├── backend/                 # Django backend
│   ├── coin_maker/         # Django project settings
│   ├── core/               # Clean architecture core
│   │   ├── interfaces/     # Abstract interfaces
│   │   ├── services/       # Business logic services
│   │   └── containers/     # Dependency injection
│   ├── apps/
│   │   ├── api/           # REST API endpoints
│   │   └── processing/    # Background tasks
│   ├── pyproject.toml
│   └── Dockerfile.prod
├── config/                 # Environment configurations
├── docs/                   # Project documentation
├── scripts/               # Deployment scripts
└── docker-compose.yml     # Production deployment
```

## Key API Endpoints

- `POST /api/upload/` - Upload original image, get generation ID
- `POST /api/process/` - Process image with parameters
- `POST /api/generate/` - Generate STL with coin parameters
- `GET /api/status/{id}/` - Check processing status
- `GET /api/download/{id}/stl` - Download generated STL
- `GET /api/preview/{id}` - Get processed heightmap image
- `GET /api/health/` - Health check endpoint

## Development Tools & Commands

### Docker Development Wrapper (`dc-dev.sh`)

The project includes a convenient Docker Compose wrapper script that simplifies development workflow:

**Key Features:**
- Automatic building before starting services
- Special shortcuts for common development tasks
- Colored output for better visibility
- Service-specific operations support
- Error handling with build validation

**Common Usage Patterns:**
```bash
# Quick start all services
./dc-dev.sh run

# Start specific services only
./dc-dev.sh run backend redis celery

# Restart after code changes
./dc-dev.sh restart backend

# Full clean rebuild (useful for dependency changes)
./dc-dev.sh recreate

# Monitor logs
./dc-dev.sh logs -f backend
./dc-dev.sh logs -f frontend-dev

# Check service status
./dc-dev.sh ps

# Standard docker compose commands also work
./dc-dev.sh exec backend python manage.py shell
./dc-dev.sh down
```

**Available Services:**
- `backend-dev` - Django development server with hot reload
- `frontend-dev` - SvelteKit dev server with HMR
- `redis` - Redis cache and message broker
- `celery-dev` - Celery worker for background tasks

## Development Commands

### Frontend
```bash
cd frontend/
pnpm install
pnpm run dev        # Development server on :5173
pnpm run build      # Production build
pnpm run check      # Type checking
```

### Backend
```bash
cd backend/
poetry install
poetry run python manage.py runserver  # Development on :8000
poetry run python manage.py migrate
```

### Docker Development
```bash
./scripts/dev-all.sh           # Start all services
./scripts/dev-backend.sh       # Backend services only

# Docker Compose Development Wrapper (Recommended)
./dc-dev.sh run                # Build and start all services in detached mode
./dc-dev.sh run backend        # Start only backend services
./dc-dev.sh restart backend    # Build and restart backend service
./dc-dev.sh recreate           # Full recreation (stop, remove, build, start)
./dc-dev.sh logs -f backend    # Follow backend logs
./dc-dev.sh ps                 # Show running services

# Direct Docker Compose
docker compose -f docker-compose.dev.yml up
```

### Production Deployment
```bash
./scripts/prod-deploy.sh       # Full production deployment
docker compose up -d --build
```

## Known Issues & Refactoring Needs

### Critical (High Priority)
1. **Monolithic Route Component** - `frontend/src/routes/+page.svelte` is 1,982 lines and handles everything (UI, canvas, API, state)
2. **State Management** - 80+ reactive variables with complex dependencies causing unnecessary re-renders
3. **Canvas Operations** - 300+ line canvas drawing functions need extraction

### Medium Priority
1. **CSS Organization** - 568+ lines of embedded CSS with duplication
2. **Error Handling** - Uses browser alerts, needs proper UI integration
3. **Accessibility** - Missing ARIA labels, keyboard navigation

### Low Priority
1. **TypeScript Strictness** - Some `any` types in Three.js code
2. **Performance** - Memory management for large images
3. **Testing** - Comprehensive test suite needed

## Configuration Files

### Environment Variables
- **Development**: `config/backend.dev.env`, `config/frontend.dev.env`
- **Production**: `config/backend.env`, `config/frontend.env`

### Key Settings
- `DEBUG=1` (dev) / `DEBUG=0` (prod)
- `MAX_GENERATIONS_PER_HOUR=100` (dev) / `20` (prod)
- `VITE_API_BASE_URL=http://localhost:8000/api`
- `SECRET_KEY` - Must change for production!

## File Processing Workflow

1. **Upload** - User uploads image via drag-and-drop
2. **Client Processing** - Frontend processes image (grayscale, brightness, contrast, gamma, invert)
3. **API Upload** - Processed image sent to backend with generation ID
4. **Heightmap Generation** - Backend creates heightmap from processed image
5. **STL Generation** - HMM + Manifold3D generates 3D model with coin parameters
6. **Download** - User downloads generated STL file

## Rate Limiting & Storage

- **Rate Limits**: 20 generations/hour per IP (production)
- **File Cleanup**: Automatic cleanup every 5 minutes for files >30 minutes old
- **Storage Location**: `/tmp/coin_maker/` with UUID-based naming
- **Max File Size**: 50MB uploads

## Testing & Quality

### Current Status
- No comprehensive test suite (high priority need)
- Manual testing workflows established
- Health checks implemented for all services

### Code Quality Tools
- **Backend**: Ruff (linting), Pyright (type checking)
- **Frontend**: TypeScript compiler, Svelte check
- **Docker**: Health checks for all containers

## Security Considerations

- Input validation on file uploads
- Rate limiting per IP address
- Process isolation for HMM execution
- No persistent user data storage
- Configurable CORS policies
- Secure default settings for production

## Performance Characteristics

- **Image Processing**: Sub-second for 4K images
- **STL Generation**: <30 seconds for typical coins
- **Memory Usage**: <512MB per operation
- **Concurrent Support**: 10 simultaneous generations

## Common Tasks for AI Agents

1. **Component Extraction** - Break down monolithic `+page.svelte`
2. **State Management** - Implement Svelte stores pattern
3. **Error Handling** - Replace alerts with proper UI notifications
4. **CSS Refactoring** - Extract styles into organized SCSS
5. **API Integration** - Enhance error handling and loading states
6. **Testing** - Add comprehensive test coverage
7. **Performance** - Optimize canvas operations and memory usage
8. **Accessibility** - Add ARIA labels and keyboard navigation

## Deployment Environments

- **Development**: Hot reloading, debug logging, relaxed limits
- **Production**: Gunicorn, nginx, health checks, security headers
- **Docker**: Multi-stage builds, non-root users, resource limits

---

*This project is a fully functional MVP ready for production deployment but could benefit from frontend refactoring and comprehensive testing.*