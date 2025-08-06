# Utility Commands
# Development tools, cleaning, and maintenance tasks

# Import all modules for cleaning
import "deps.just"
import "frontend.just"
import "backend.just"
import "desktop-artifacts.just"
import "docker.just"

# Clean everything (complete cleanup)
clean:
    #!/usr/bin/env bash
    set -e
    echo "Cleaning all build artifacts and caches..."
    
    # Clean all build directories
    echo "Cleaning build directories..."
    rm -rf build/web_*
    rm -rf build/desktop_*
    rm -rf build/artifacts
    
    # Clean source directories
    echo "Cleaning source build artifacts..."
    rm -rf frontend/build
    rm -rf frontend/.svelte-kit
    rm -rf frontend/dist
    
    # Clean backend Python cache
    echo "Cleaning backend Python cache..."
    cd backend
    rm -rf __pycache__
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    rm -rf dist
    rm -rf build
    cd ..
    
    # Clean Docker resources
    echo "Cleaning Docker resources..."
    just clean-web-docker
    
    # Clean third-party dependencies
    echo "Cleaning third-party dependencies..."
    just clean-deps
    
    # Clean temporary files
    echo "Cleaning temporary files..."
    rm -rf temp/*
    rm -rf backend/temp/*
    rm -rf logs/*
    
    echo "Complete cleanup finished"

# Clean specific target
# Usage: just clean-target frontend
clean-target target:
    #!/usr/bin/env bash
    set -e
    
    case "{{target}}" in
        "deps"|"dependencies")
            echo "Cleaning dependencies..."
            just clean-deps
            ;;
        "frontend")
            echo "Cleaning all frontend builds..."
            just clean-frontend
            ;;
        "backend")
            echo "Cleaning all backend builds..."
            just clean-backend
            ;;
        "desktop")
            echo "Cleaning desktop builds..."
            just clean-desktop
            ;;
        "docker")
            echo "Cleaning Docker resources..."
            just clean-web-docker
            ;;
        "appimage")
            echo "Cleaning AppImage artifacts..."
            just clean-desktop-appimage
            ;;
        "flatpak")
            echo "Cleaning Flatpak artifacts..."
            just clean-desktop-flatpak
            ;;
        "artifacts")
            echo "Cleaning all artifacts..."
            rm -rf build/artifacts
            ;;
        "temp"|"temporary")
            echo "Cleaning temporary files..."
            rm -rf temp/*
            rm -rf backend/temp/*
            rm -rf logs/*
            ;;
        *)
            echo "Error: Unknown target '{{target}}'"
            echo "Available targets: deps, frontend, backend, desktop, docker, appimage, flatpak, artifacts, temp"
            exit 1
            ;;
    esac

# Format code
format:
    #!/usr/bin/env bash
    set -e
    echo "Formatting code..."
    
    # Backend formatting
    echo "Formatting backend code..."
    cd backend
    if poetry run which ruff &> /dev/null; then
        poetry run ruff format .
    else
        echo "Warning: ruff not found, skipping backend formatting"
    fi
    cd ..
    
    # Frontend formatting
    echo "Formatting frontend code..."
    cd frontend
    if command -v prettier &> /dev/null; then
        prettier --write src/
    elif pnpm list prettier &> /dev/null; then
        pnpm exec prettier --write src/
    else
        echo "Warning: prettier not found, skipping frontend formatting"
    fi
    cd ..
    
    echo "Code formatting complete"

# Lint code
lint:
    #!/usr/bin/env bash
    set -e
    echo "Linting code..."
    
    # Backend linting
    echo "Linting backend code..."
    cd backend
    if poetry run which ruff &> /dev/null; then
        poetry run ruff check .
    else
        echo "Warning: ruff not found, skipping backend linting"
    fi
    
    if poetry run which pyright &> /dev/null; then
        poetry run pyright .
    else
        echo "Warning: pyright not found, skipping backend type checking"
    fi
    cd ..
    
    # Frontend linting
    echo "Linting frontend code..."
    cd frontend
    if pnpm list eslint &> /dev/null; then
        pnpm run lint
    elif grep -q "lint" package.json; then
        pnpm run lint
    else
        echo "Warning: frontend linting not configured"
    fi
    cd ..
    
    echo "Code linting complete"

# Type check code
typecheck:
    #!/usr/bin/env bash
    set -e
    echo "Type checking code..."
    
    # Backend type checking
    echo "Type checking backend..."
    cd backend
    if poetry run which pyright &> /dev/null; then
        poetry run pyright .
    else
        echo "Warning: pyright not found, skipping backend type checking"
    fi
    cd ..
    
    # Frontend type checking
    echo "Type checking frontend..."
    cd frontend
    if pnpm list typescript &> /dev/null || grep -q "check" package.json; then
        pnpm run check
    else
        echo "Warning: frontend type checking not configured"
    fi
    cd ..
    
    echo "Type checking complete"

# Run tests
test:
    #!/usr/bin/env bash
    set -e
    echo "Running tests..."
    
    # Backend tests
    echo "Running backend tests..."
    cd backend
    if poetry run which pytest &> /dev/null; then
        poetry run pytest
    else
        echo "Warning: pytest not found, skipping backend tests"
    fi
    cd ..
    
    # Frontend tests
    echo "Running frontend tests..."
    cd frontend
    if grep -q "test" package.json; then
        pnpm test
    else
        echo "Warning: frontend tests not configured"
    fi
    cd ..
    
    echo "All tests complete"

# Security audit
audit:
    #!/usr/bin/env bash
    set -e
    echo "Running security audit..."
    
    # Backend security audit
    echo "Auditing backend dependencies..."
    cd backend
    if poetry run which safety &> /dev/null; then
        poetry run safety check
    else
        echo "Warning: safety not installed for Python audit"
        echo "Install with: poetry add --group=dev safety"
    fi
    cd ..
    
    # Frontend security audit
    echo "Auditing frontend dependencies..."
    cd frontend
    pnpm audit
    cd ..
    
    echo "Security audit complete"

# Show project information  
project-info:
    #!/usr/bin/env bash
    echo "Coin Maker Project Information"
    echo "=============================="
    echo ""
    
    # Project version
    if [ -f "frontend/package.json" ]; then
        version=$(grep '"version"' frontend/package.json | cut -d'"' -f4)
        echo "Project Version: $version"
    fi
    
    # Git information
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo "Git Branch: $(git branch --show-current)"
        echo "Git Commit: $(git rev-parse --short HEAD)"
        echo "Git Status: $(git status --porcelain | wc -l) modified files"
    fi
    
    echo ""
    echo "Build Structure:"
    echo "==============="
    
    # Show build directories if they exist
    if [ -d "build" ]; then
        echo "Available builds:"
        find build -maxdepth 1 -type d -name "*_*_*" | sort
    else
        echo "No builds found (run build commands to create)"
    fi
    
    # Show artifacts
    if [ -d "build/artifacts" ]; then
        echo ""
        echo "Available artifacts:"
        ls -la build/artifacts/ 2>/dev/null || echo "No artifacts found"
    fi
    
    echo ""
    echo "System Information:"
    echo "=================="
    echo "Platform: $(uname -s) $(uname -m)"
    echo "Python: $(python3 --version 2>&1)"
    
    if command -v node &> /dev/null; then
        echo "Node: $(node --version)"
    fi
    
    if command -v docker &> /dev/null; then
        echo "Docker: $(docker --version | cut -d',' -f1)"
    fi

# Show available configurations
list-configs:
    #!/usr/bin/env bash
    echo "Available Build Configurations"
    echo "=============================="
    echo ""
    echo "Desktop Configurations:"
    echo "  mode: debug, release"
    echo "  variant: desktop (always)"
    echo "  scheduler: apscheduler (always)"
    echo ""
    echo "Web Configurations:"
    echo "  mode: debug, release"
    echo "  variant: web (always)"
    echo "  scheduler: apscheduler, celery"
    echo ""
    echo "Available Build Commands:"
    echo "  MODE=<mode> VARIANT=<variant> just build-frontend"
    echo "  MODE=<mode> VARIANT=<variant> SCHEDULER=<scheduler> just build-backend"
    echo "  MODE=<mode> just build-desktop"
    echo "  MODE=<mode> SCHEDULER=<scheduler> just build-web-docker"
    echo ""
    echo "Available Run Commands:"
    echo "  MODE=<mode> just run-desktop-local"
    echo "  MODE=<mode> just run-desktop"
    echo "  just run-desktop-appimage"
    echo "  just run-desktop-flatpak"
    echo "  MODE=<mode> SCHEDULER=<scheduler> just run-web-local"
    echo "  MODE=<mode> SCHEDULER=<scheduler> just run-web-docker"

# Quick development setup (utilities version)
util-dev-setup:
    #!/usr/bin/env bash
    set -e
    echo "Setting up development environment..."
    
    # Install dependencies
    just install-deps
    
    # Build essential dependencies
    just build-deps
    
    echo ""
    echo "Development setup complete!"
    echo ""
    echo "Quick start options:"
    echo "  Desktop: just run-desktop-local"
    echo "  Web:     just run-web-local"
    echo "  Docker:  just run-web-docker"