# Coin Maker Build System
# Modular task runner for desktop and web builds

# Import all modules
import "build-scripts/dependencies.just"
import "build-scripts/frontend.just"
import "build-scripts/desktop.just"
import "build-scripts/docker.just"
import "build-scripts/packaging.just"
import "build-scripts/utilities.just"
import "build-scripts/smoke-tests.just"

# Configuration variables
config_mode := env_var_or_default('MODE', 'dev')

# Show available commands
default:
    @just --list

# =============================================================================
# Quick Start Commands
# =============================================================================

# Complete development environment setup
dev-setup: install-deps build-hmm
    echo "Development setup complete! Run 'just run-desktop' to start."

# Quick development build (frontend + dependencies)
dev-build: install-deps build-frontend

# Quick production build (everything for deployment)
prod-build mode="prod": (build-desktop mode)

# Quick Docker development start
docker-dev profile="": (run-docker-detached "dev" profile)

# Quick Docker production start  
docker-prod profile="": (run-docker-detached "prod" profile)

# =============================================================================
# Workflow Shortcuts
# =============================================================================

# Full development workflow: setup, build, and run
dev: dev-setup run-desktop

# Full production workflow: build and package
prod: prod-build build-appimage

# Full Flatpak workflow: build and export bundle
flatpak: build-flatpak export-flatpak

# Quick test workflow: format, lint, and test
ci: format lint test

# =============================================================================
# Help and Information
# =============================================================================

# Show detailed help for all commands
help:
    #!/usr/bin/env bash
    echo "Coin Maker Build System - Modular Just Tasks"
    echo "============================================="
    echo ""
    echo "QUICK START:"
    echo "  just dev-setup     # Setup development environment"
    echo "  just run-desktop   # Run desktop app"
    echo "  just run-docker    # Run with Docker"
    echo "  just flatpak       # Build and export Flatpak package"
    echo ""
    echo "BUILDING:"
    echo "  just build-frontend [mode]  # Build frontend (dev/prod/desktop)"
    echo "  just build-desktop [mode]   # Build desktop app"
    echo "  just build-appimage         # Create Linux AppImage"
    echo "  just build-flatpak          # Create Flatpak package"
    echo ""
    echo "DOCKER:"
    echo "  just docker-dev [profile]         # Start dev containers (quick)"
    echo "  just docker-prod [profile]        # Start prod containers (quick)"
    echo "  just run-docker [mode] [profile]  # Start containers (full control)"
    echo "  just stop-docker [mode] [profile] # Stop containers"
    echo "  just docker-logs [mode] [profile] [service]  # View logs"
    echo "  just restart-docker [mode] [profile] [service]  # Restart services"
    echo "  just docker-status [mode] [profile]  # Show container status"
    echo "  just test-docker-config [mode] [profile]  # Test configuration"
    echo "  just clean-docker              # Clean Docker resources"
    echo ""
    echo "   Docker Profiles: celery, apscheduler (default: none)"
    echo "   Docker Modes: dev, prod (default: dev)"
    echo ""
    echo "SMOKE TESTS:"
    echo "  just smoke-test [browser] [filter]    # Run all smoke tests"
    echo "  just smoke-test-quick             # Quick test (one config)"
    echo "  just smoke-test-web [browser]     # Test web configurations"
    echo "  just smoke-test-docker [browser]  # Test Docker configurations"
    echo "  just smoke-test-desktop [browser] # Test desktop configurations"
    echo "  just smoke-test-list              # List available configurations"
    echo "  just smoke-test-check             # Check requirements"
    echo "  just smoke-test-install           # Install dependencies"
    echo ""
    echo "UTILITIES:"
    echo "  just clean          # Clean build artifacts"
    echo "  just format         # Format code"
    echo "  just lint           # Lint code"
    echo "  just test           # Run tests"
    echo "  just check-deps     # Check system dependencies"
    echo ""
    echo "DEPENDENCIES:"
    echo "  just build-hmm      # Build HMM library"
    echo "  just install-deps   # Install all dependencies"
    echo ""
    echo "PACKAGING:"
    echo "  just create-pyinstaller-spec  # Create PyInstaller spec"
    echo "  just create-desktop-file      # Create AppImage desktop file"
    echo "  just install-flatpak          # Install Flatpak locally for testing"
    echo "  just export-flatpak           # Export Flatpak bundle for distribution"
    echo ""
    echo "For detailed command info: just --list"

# Show version information
version:
    #!/usr/bin/env bash
    echo "Coin Maker Build System"
    echo "======================="
    
    # Project version (from package.json)
    if [ -f "frontend/package.json" ]; then
        version=$(grep '"version"' frontend/package.json | cut -d'"' -f4)
        echo "Project Version: $version"
    fi
    
    # Tool versions
    echo ""
    echo "Build Tools:"
    just --version
    
    if command -v poetry &> /dev/null; then
        poetry --version
    fi
    
    if command -v pnpm &> /dev/null; then
        pnpm --version
    fi
    
    if command -v docker &> /dev/null; then
        docker --version
    fi
    
    # System info
    echo ""
    echo "System: $(uname -s) $(uname -m)"
    echo "Python: $(python3 --version 2>&1)"
    
    if command -v node &> /dev/null; then
        echo "Node: $(node --version)"
    fi

# Show project structure
info:
    #!/usr/bin/env bash
    echo "Project Structure:"
    echo "=================="
    echo ""
    echo "Project Layout:"
    tree -L 2 -I 'node_modules|__pycache__|.git|build|dist|temp|logs|external' . || \
    find . -maxdepth 2 -type d -not -path '*/.*' -not -path '*/node_modules*' -not -path '*/__pycache__*' | sort
    echo ""
    echo "Build Scripts:"
    ls -la build-scripts/
    echo ""
    echo "Available Modes: dev, prod, desktop"
    echo "Current Mode: $MODE (default: dev)"