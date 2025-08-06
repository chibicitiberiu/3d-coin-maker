# Configuration and Version Management
# Project metadata and versioning

# Project information
PROJECT_NAME = coin-maker
PROJECT_DESCRIPTION = AI-powered 3D printable coin generator

# Version information
VERSION_MAJOR = 1
VERSION_MINOR = 0
VERSION_PATCH = 0

# Computed version strings
VERSION_MAJOR_ONLY = $(VERSION_MAJOR)
VERSION = $(VERSION_MAJOR).$(VERSION_MINOR)
VERSION_FULL = $(VERSION).$(VERSION_PATCH)

# Registry configuration
DEFAULT_REGISTRY = docker.io
DEFAULT_NAMESPACE = coinmaker

# Feature flags (can be overridden from command line)
ENABLE_FLATPAK ?= true

# Image naming with version support
DOCKER_IMAGE_PREFIX = coinmaker
DOCKER_VERSION_TAG = $(VERSION)
DOCKER_VERSION_FULL_TAG = $(VERSION_FULL)

# Mode-specific version tags
DOCKER_SCHEDULER_TAG = $(if $(filter release,$(MODE)),$(VERSION)-$(SCHEDULER),$(VERSION)-$(SCHEDULER)-debug)

# Final image names
DOCKER_IMAGE_FRONTEND = $(DOCKER_IMAGE_PREFIX)-frontend:$(if $(filter release,$(MODE)),$(VERSION),$(VERSION)-debug)
DOCKER_IMAGE_BACKEND = $(DOCKER_IMAGE_PREFIX)-backend:$(DOCKER_SCHEDULER_TAG)
DOCKER_IMAGE_CELERY_WORKER = $(DOCKER_IMAGE_PREFIX)-celery-worker:$(if $(filter release,$(MODE)),$(VERSION),$(VERSION)-debug)
DOCKER_IMAGE_CELERY_BEAT = $(DOCKER_IMAGE_PREFIX)-celery-beat:$(if $(filter release,$(MODE)),$(VERSION),$(VERSION)-debug)

# Build metadata
BUILD_DATE = $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")
BUILD_USER = $(shell whoami)
BUILD_HOST = $(shell hostname)

# Git information (if available)
GIT_COMMIT = $(shell git rev-parse HEAD 2>/dev/null || echo "unknown")
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
GIT_TAG = $(shell git describe --tags --exact-match 2>/dev/null || echo "")
GIT_DIRTY = $(shell git diff --quiet 2>/dev/null || echo "-dirty")

# Print configuration
print-version:
	$(call log_section_start,Version Configuration)
	$(call log_info,PROJECT_NAME     = $(PROJECT_NAME))
	$(call log_info,VERSION          = $(VERSION))
	$(call log_info,VERSION_FULL     = $(VERSION_FULL))
	$(call log_info,BUILD_DATE       = $(BUILD_DATE))
	$(call log_info,BUILD_USER       = $(BUILD_USER))
	$(call log_info,BUILD_HOST       = $(BUILD_HOST))
	@echo ""
	$(call log_info,Docker Images (MODE=$(MODE), SCHEDULER=$(SCHEDULER)):)
	$(call log_info,FRONTEND         = $(DOCKER_IMAGE_FRONTEND))
	$(call log_info,BACKEND          = $(DOCKER_IMAGE_BACKEND))
	@if [ "$(SCHEDULER)" = "celery" ]; then \
		$(call log_info,CELERY_WORKER    = $(DOCKER_IMAGE_CELERY_WORKER)); \
		$(call log_info,CELERY_BEAT      = $(DOCKER_IMAGE_CELERY_BEAT)); \
	fi

.PHONY: print-version