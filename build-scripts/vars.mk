# Build System Variables
# Centralized path definitions and variable calculations

# Default parameter values
MODE ?= debug
SCHEDULER ?= apscheduler

# Base directories
BUILD_ROOT = build

# Configuration-specific build directories
BUILD_DIR = $(BUILD_ROOT)/$(MODE)

# Component directories
FRONTEND_SRC = frontend
BUILD_FRONTEND = $(BUILD_DIR)/frontend

BACKEND_SRC = backend
BUILD_BACKEND = $(BUILD_DIR)/backend

# Third parties
EXTERNAL_SRC = external
BUILD_EXTERNAL = $(BUILD_ROOT)/external

BUILD_HMM = $(BUILD_EXTERNAL)/hmm
BUILD_HMM_BINARY = $(BUILD_HMM)/hmm

# NPM/Poetry mode mapping
NPM_MODE = $(if $(filter debug,$(MODE)),development,production)
POETRY_ENV = $(if $(filter debug,$(MODE)),development,production)

# PNPM common arguments
PNPM_INSTALL_ARGS = --frozen-lockfile --prefer-offline

# Boolean flags for configuration
DEBUG_FLAG = $(if $(filter debug,$(MODE)),true,false)
CELERY_FLAG = $(if $(filter celery,$(SCHEDULER)),true,false)


# Runtime port configuration
BACKEND_PORT ?= 8001

# Docker image naming (scheduler affects image names but not build dirs)
DOCKER_IMAGE_TAG = $(MODE)_$(SCHEDULER)

# Validation functions
validate-mode:
	@if [ "$(MODE)" != "debug" ] && [ "$(MODE)" != "release" ]; then \
		echo "Error: MODE must be 'debug' or 'release', got '$(MODE)'"; \
		exit 1; \
	fi

validate-scheduler:
	@if [ "$(SCHEDULER)" != "apscheduler" ] && [ "$(SCHEDULER)" != "celery" ]; then \
		echo "Error: SCHEDULER must be 'apscheduler' or 'celery', got '$(SCHEDULER)'"; \
		exit 1; \
	fi

validate-all: validate-mode validate-scheduler

# Display current configuration
print-config:
	$(call log_section_start,Build Configuration)
	$(call log_info,MODE      = $(MODE) (build-time))
	$(call log_info,SCHEDULER = $(SCHEDULER) (runtime-only))
	@echo ""
	$(call log_info,Build Directories:)
	$(call log_info,BUILD_DIR      = $(BUILD_DIR))
	$(call log_info,BUILD_FRONTEND = $(BUILD_FRONTEND))
	$(call log_info,BUILD_BACKEND  = $(BUILD_BACKEND))
	$(call log_info,BUILD_HMM      = $(BUILD_HMM))
	@echo ""
	$(call log_info,Docker Image:)
	$(call log_info,DOCKER_IMAGE_TAG = $(DOCKER_IMAGE_TAG))
	@echo ""
	$(call log_info,Runtime Flags:)
	$(call log_info,DEBUG_FLAG   = $(DEBUG_FLAG))
	$(call log_info,CELERY_FLAG  = $(CELERY_FLAG))

.PHONY: print-config validate-mode validate-scheduler validate-all