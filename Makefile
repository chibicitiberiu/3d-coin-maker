# Coin Maker Build System
# Make variable driven build system with proper dependency management

# Include centralized variables and path definitions
include build-scripts/vars.mk
include build-scripts/config.mk
include build-scripts/make-output.mk

# Dependencies
include build-scripts/deps.mk
include build-scripts/deps-system.mk
include build-scripts/frontend.mk  
include build-scripts/backend.mk
include build-scripts/desktop.mk
include build-scripts/docker.mk
include build-scripts/appimage.mk

# Default target
.DEFAULT_GOAL := help

help:
	@echo "Coin Maker Build System"
	@echo "======================="
	@echo ""
	@echo "Usage: make <target> MODE=debug SCHEDULER=apscheduler BACKEND_PORT=8001"
	@echo ""
	@echo "Parameters:"
	@echo "  MODE              = debug | release (default: debug)"
	@echo "  SCHEDULER         = apscheduler | celery (runtime-only)"
	@echo "  BACKEND_PORT      = port for backend server (default: 8001)"
	@echo ""
	@echo "Main targets:"
	@echo "  build-frontend       Build frontend for specified configuration"
	@echo "  build-backend        Build backend for specified configuration"
	@echo "  build-desktop        Build desktop environment and dependencies"
	@echo "  build-appimage       Build AppImage for desktop (auto-detects Python version)"
	@echo "  run-frontend-dev     Run frontend in development mode with live reload"
	@echo "  run-frontend         Run built frontend (after build-frontend)"
	@echo "  run-backend          Run backend with specified scheduler"
	@echo "  run-desktop          Run desktop application"
	@echo "  run                  Run both frontend and backend in parallel"
	@echo "  run-dev              Run frontend dev server and backend in parallel"
	@echo "  clean-frontend       Clean frontend builds"
	@echo "  clean-backend        Clean backend builds"
	@echo "  clean-desktop        Clean desktop environment"
	@echo "  clean-appimage       Clean AppImage artifacts"
	@echo "  clean                Clean everything"
	@echo "  clean-all            Clean everything including build directory"
	@echo "  venv-backend         Activate backend virtual environment"
	@echo "  venv-desktop         Activate desktop virtual environment"
	@echo ""
	@echo "Docker targets:"
	@echo "  build-web-docker     Build Docker images for web deployment"
	@echo "  publish-web-docker   Build and tag Docker images for publishing"
	@echo "  run-web-docker       Start web application in Docker (foreground)"
	@echo "  run-web-docker-detached  Start web application in Docker (background)"
	@echo "  stop-web-docker      Stop Docker containers"
	@echo "  docker-logs          Show Docker container logs"
	@echo "  docker-status        Show Docker container status"
	@echo "  clean-web-docker     Clean Docker images and containers"
	@echo ""
	@echo "Dependencies and tools:"
	@echo "  build-deps           Build custom dependencies (like hmm binary)"
	@echo "  clean-deps           Clean built dependencies"
	@echo "  install-system-deps  Install system dependencies (requires sudo)"
	@echo "  check-system-deps    Check if system dependencies are installed"
	@echo ""
	@echo "Utilities:"
	@echo "  print-config         Display current build configuration"
	@echo "  print-version        Display version and Docker image information"
	@echo ""
	@echo "Examples:"
	@echo "  make build-frontend                                    # debug frontend"
	@echo "  make build-frontend MODE=release                      # release frontend"
	@echo "  make build-backend MODE=debug                         # debug backend"
	@echo "  make run-backend MODE=debug SCHEDULER=celery          # run backend with celery"
	@echo "  make run-dev                                           # run frontend dev + backend"
	@echo "  make run MODE=release                                  # run built frontend + backend"
	@echo "  make run-dev BACKEND_PORT=9000                         # run with custom backend port"
	@echo "  make run-desktop                                       # run desktop application"
	@echo "  make build-appimage MODE=release                      # build release AppImage"
	@echo "  make build-appimage MODE=debug                        # build debug AppImage"
	@echo "  make build-web-docker MODE=release SCHEDULER=celery   # build production Docker with celery"
	@echo "  make run-web-docker MODE=debug SCHEDULER=apscheduler  # run development Docker"
	@echo ""
	@echo "For Docker/publish targets that need specific configs, use recursive make:"
	@echo "  \$$(MAKE) build-backend MODE=release                   # from other targets"

run: build-frontend build-backend build-deps
	$(call log_section_start,Starting Full Application)
	$(call show_build_config)
	$(call log_step,Launching frontend (preview) and backend services)
	@export BUILD_DIR="$(BUILD_DIR)" && \
	export BUILD_BACKEND_CONFIG="$(BUILD_BACKEND_CONFIG)" && \
	export BACKEND_SRC="$(BACKEND_SRC)" && \
	export FRONTEND_SRC="$(FRONTEND_SRC)" && \
	export HMM_BINARY_PATH="$(BUILD_HMM_BINARY)" && \
	export NPM_MODE="$(NPM_MODE)" && \
	./scripts/run-wrapper.sh --mode $(MODE) --scheduler $(SCHEDULER) --backend-port $(BACKEND_PORT) --frontend-type preview

run-dev: $(FRONTEND_SRC)/node_modules build-backend build-deps
	$(call log_section_start,Starting Development Environment)
	$(call show_build_config)
	$(call log_step,Launching frontend dev server and backend services)
	@export BUILD_DIR="$(BUILD_DIR)" && \
	export BUILD_BACKEND_CONFIG="$(BUILD_BACKEND_CONFIG)" && \
	export BACKEND_SRC="$(BACKEND_SRC)" && \
	export FRONTEND_SRC="$(FRONTEND_SRC)" && \
	export HMM_BINARY_PATH="$(BUILD_HMM_BINARY)" && \
	export NPM_MODE="$(NPM_MODE)" && \
	./scripts/run-wrapper.sh --mode $(MODE) --scheduler $(SCHEDULER) --backend-port $(BACKEND_PORT) --frontend-type dev

clean: clean-frontend clean-backend clean-desktop clean-appimage
	$(call log_target_complete,Clean All Components)

clean-all: clean
	$(call log_step,Removing entire build directory)
	@rm -rf build/
	$(call log_target_complete,Deep Clean)

.PHONY: help clean clean-all run run-dev