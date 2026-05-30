# Coin Maker Build System - Refactored
# Modular, consistent, and maintainable build system with proper dependency management

# Import all modules
import "build-scripts/deps.just"
import "build-scripts/frontend.just"
import "build-scripts/backend.just"
import "build-scripts/desktop-artifacts.just"
import "build-scripts/docker.just"
import "build-scripts/run.just"
import "build-scripts/utilities.just"
import "build-scripts/smoke-test.just"

# =============================================================================
# Parameter Validation Functions
# =============================================================================

# Validate MODE parameter (debug or release)
_validate-mode:
    #!/usr/bin/env bash
    mode="${MODE:-debug}"
    if [[ "$mode" != "debug" && "$mode" != "release" ]]; then
        echo "Error: MODE must be 'debug' or 'release', got '$mode'"
        exit 1
    fi

# Validate VARIANT parameter (web or desktop)
_validate-variant:
    #!/usr/bin/env bash
    variant="${VARIANT:-web}"
    if [[ "$variant" != "web" && "$variant" != "desktop" ]]; then
        echo "Error: VARIANT must be 'web' or 'desktop', got '$variant'"
        exit 1
    fi

# Validate SCHEDULER parameter (apscheduler or celery)
_validate-scheduler:
    #!/usr/bin/env bash
    scheduler="${SCHEDULER:-apscheduler}"
    if [[ "$scheduler" != "apscheduler" && "$scheduler" != "celery" ]]; then
        echo "Error: SCHEDULER must be 'apscheduler' or 'celery', got '$scheduler'"
        exit 1
    fi

# Validate desktop+scheduler combination (desktop only supports apscheduler)
_validate-desktop-scheduler:
    #!/usr/bin/env bash
    variant="${VARIANT:-web}"
    scheduler="${SCHEDULER:-apscheduler}"
    if [ "$variant" = "desktop" ] && [ "$scheduler" != "apscheduler" ]; then
        echo "Error: Desktop variant only supports apscheduler scheduler, got '$scheduler'"
        exit 1
    fi

# Validate all common parameters
_validate-all: _validate-mode _validate-variant _validate-scheduler _validate-desktop-scheduler

# Show available commands (default when running 'just')
default:
    @just --list

# =============================================================================
# Quick Workflow Commands
# =============================================================================

# Complete development environment setup
dev-setup:
    just install-deps
    just build-deps
    echo "Development setup complete!"
    echo ""
    echo "Quick start options:"
    echo "  Desktop: just run-desktop-local"
    echo "  Web:     just run-web-local"
    echo "  Docker:  just run-web-docker"

# Quick development workflow - desktop
dev-desktop mode="debug":
    just run-desktop-local mode="{{mode}}"

# Quick development workflow - web local
dev-web mode="debug" scheduler="apscheduler":
    just run-web-local mode="{{mode}}" scheduler="{{scheduler}}"

# Quick development workflow - web docker
dev-web-docker mode="debug" scheduler="apscheduler":
    just run-web-docker mode="{{mode}}" scheduler="{{scheduler}}"

# Quick release build - desktop with AppImage
release-desktop:
    just build-desktop mode="release"
    just build-desktop-appimage mode="release"
    echo "Desktop release complete:"
    echo "  Binary: build/desktop_release_apscheduler/"
    echo "  AppImage: build/artifacts/CoinMaker-$(arch).AppImage"

# Quick release build - web docker
release-web scheduler="celery":
    just build-web-docker mode="release" scheduler="{{scheduler}}"
    echo "Web release complete - Docker images built:"
    echo "  coinmaker:web_release_{{scheduler}}"

# Complete release build - all artifacts
release-all:
    just release-desktop
    just release-web
    just build-desktop-flatpak mode="release"
    echo "All release artifacts complete!"

# =============================================================================
# Testing Workflows
# =============================================================================

# Quick smoke test
test-quick browser="chrome":
    just smoke-test-quick browser="{{browser}}"

# Full test suite
test-all browser="chrome":
    just format
    just lint
    just typecheck
    just test
    just smoke-test-all browser="{{browser}}"

# Test specific configuration
test-config mode="debug" variant="web" scheduler="apscheduler" browser="chrome":
    just smoke-test mode="{{mode}}" variant="{{variant}}" scheduler="{{scheduler}}" browser="{{browser}}"

# =============================================================================
# CI/CD Workflows
# =============================================================================

# Complete CI workflow
ci browser="chrome":
    just format
    just lint  
    just typecheck
    just test
    just smoke-test-web browser="{{browser}}"
    just smoke-test-desktop browser="{{browser}}"

# Build all configurations for CI
ci-build:
    echo "Building all configurations for CI..."
    
    # Desktop configurations
    just build-desktop mode="debug"
    just build-desktop mode="release"
    
    # Web configurations  
    just build-web-docker mode="debug" scheduler="apscheduler"
    just build-web-docker mode="debug" scheduler="celery"
    just build-web-docker mode="release" scheduler="apscheduler"
    just build-web-docker mode="release" scheduler="celery"
    
    echo "All CI builds complete!"

# Publish all release artifacts
publish registry="":
    #!/usr/bin/env bash
    set -e
    
    # Docker images
    just publish-web-docker mode="release" scheduler="apscheduler" registry="{{registry}}"
    just publish-web-docker mode="release" scheduler="celery" registry="{{registry}}"
    
    # Desktop artifacts are built locally - copy to distribution directory
    mkdir -p dist/
    if [ -f "build/artifacts/CoinMaker-$(arch).AppImage" ]; then
        cp build/artifacts/CoinMaker-$(arch).AppImage dist/
    fi
    if [ -f "build/artifacts/CoinMaker-$(arch).flatpak" ]; then
        cp build/artifacts/CoinMaker-$(arch).flatpak dist/
    fi
    
    echo "All artifacts published!"

# =============================================================================
# Information and Help
# =============================================================================

# Show project and build information
info:
    just -f build-scripts/utilities-new.just project-info

# Show available build configurations
configs:
    just list-configs

# Show smoke test configurations
test-configs:
    just smoke-test-list

# Show current build status
status:
    #!/usr/bin/env bash
    echo "Coin Maker Build Status"
    echo "======================"
    echo ""
    
    # Show available builds
    if [ -d "build" ]; then
        echo "Available builds:"
        find build -maxdepth 1 -type d -name "*_*_*" | sort | while read -r dir; do
            config=$(basename "$dir")
            echo "  ✓ $config"
        done
    else
        echo "No builds found"
    fi
    
    # Show available artifacts
    if [ -d "build/artifacts" ] && [ "$(ls -A build/artifacts 2>/dev/null)" ]; then
        echo ""
        echo "Available artifacts:"
        ls -la build/artifacts/ | grep -v "^total" | awk '{print "  " $9 " (" $5 " bytes)"}'
    fi
    
    # Show Docker images
    echo ""
    echo "Docker images:"
    docker images --format "table {{{{.Repository}}}}:{{{{.Tag}}}}\t{{{{.Size}}}}" | grep "coinmaker" || echo "  No coinmaker images found"

# =============================================================================
# Compatibility Aliases (for migration period)
# =============================================================================

# Legacy command aliases to ease migration
alias build-hmm := build-deps

# Legacy workflow aliases
alias dev := dev-desktop
alias prod := release-desktop