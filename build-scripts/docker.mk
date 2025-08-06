# Docker Web Application Management
# Builds and manages Docker containers with proper dependency management

# Docker image naming is now handled in config.mk
# Legacy compatibility
DEFAULT_REGISTRY = docker.io

# Helper function to build docker-compose command
define docker-compose-cmd
	$(eval export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development))
	$(eval export SCHEDULER=$(SCHEDULER))
	$(if $(filter debug,$(MODE)),\
		$(if $(filter celery,$(SCHEDULER)),docker compose -f docker-compose.yml -f docker-compose.override.yml --profile celery,\
		$(if $(filter apscheduler,$(SCHEDULER)),docker compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.apscheduler.yml,\
		docker compose -f docker-compose.yml -f docker-compose.override.yml)),\
		$(if $(filter celery,$(SCHEDULER)),docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile celery,\
		$(if $(filter apscheduler,$(SCHEDULER)),docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.apscheduler.yml,\
		docker compose -f docker-compose.yml -f docker-compose.prod.yml)))
endef

build-frontend-docker: validate-all
	$(call log_target_start,Building Frontend Docker Image)
	@$(MAKE) build-frontend VARIANT=web
	$(call log_step,Building Docker image (this may take a moment))
	@export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development); \
	docker build -f frontend/Dockerfile \
		--build-arg ENVIRONMENT=$$ENVIRONMENT \
		--target $(if $(filter release,$(MODE)),production,development) \
		-t coin-maker-frontend:temp \
		frontend/
	@$(MAKE) _tag-frontend-image
	$(call log_target_complete,Frontend Docker Image: $(DOCKER_IMAGE_FRONTEND))

build-backend-docker: validate-all build-deps
	$(call log_target_start,Building Backend Docker Image)
	@$(MAKE) build-backend VARIANT=web
	$(call log_step,Building Docker image (this may take a moment))
	@export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development); \
	export USE_CELERY=$(if $(filter celery,$(SCHEDULER)),true,false); \
	docker build -f backend/Dockerfile \
		--build-arg ENVIRONMENT=$$ENVIRONMENT \
		--build-arg USE_CELERY=$$USE_CELERY \
		-t coin-maker-backend:temp \
		backend/
	@$(MAKE) _tag-backend-images
	$(call log_target_complete,Backend Docker Image: $(DOCKER_IMAGE_BACKEND))
	@if [ "$(SCHEDULER)" = "celery" ]; then \
		$(call log_info,Celery Worker: $(DOCKER_IMAGE_CELERY_WORKER)); \
		$(call log_info,Celery Beat: $(DOCKER_IMAGE_CELERY_BEAT)); \
	fi

build-docker: build-frontend-docker build-backend-docker
	$(call log_section_start,Docker Build Complete)
	$(call log_info,Frontend: $(DOCKER_IMAGE_FRONTEND))
	$(call log_info,Backend: $(DOCKER_IMAGE_BACKEND))
	@if [ "$(SCHEDULER)" = "celery" ]; then \
		$(call log_info,Celery Worker: $(DOCKER_IMAGE_CELERY_WORKER)); \
		$(call log_info,Celery Beat: $(DOCKER_IMAGE_CELERY_BEAT)); \
	fi

publish-docker: validate-all build-docker
	@registry="$(if $(REGISTRY),$(REGISTRY),$(DEFAULT_REGISTRY))"; \
	echo "Publishing Docker images to $$registry ($(MODE) mode, $(SCHEDULER) scheduler)..."; \
	\
	frontend_tag="$(DOCKER_IMAGE_FRONTEND)"; \
	frontend_remote="$$registry/$(DOCKER_IMAGE_FRONTEND)"; \
	echo "Pushing $$frontend_tag -> $$frontend_remote"; \
	docker tag "$$frontend_tag" "$$frontend_remote"; \
	docker push "$$frontend_remote"; \
	\
	backend_tag="$(DOCKER_IMAGE_BACKEND)"; \
	backend_remote="$$registry/$(DOCKER_IMAGE_BACKEND)"; \
	echo "Pushing $$backend_tag -> $$backend_remote"; \
	docker tag "$$backend_tag" "$$backend_remote"; \
	docker push "$$backend_remote"; \
	\
	if [ "$(SCHEDULER)" = "apscheduler" ] && [ "$(MODE)" = "release" ]; then \
		latest_tag="$$registry/coinmaker-backend:latest"; \
		echo "Pushing $$backend_tag -> $$latest_tag (default)"; \
		docker tag "$$backend_tag" "$$latest_tag"; \
		docker push "$$latest_tag"; \
	fi; \
	\
	if [ "$(SCHEDULER)" = "celery" ]; then \
		worker_tag="$(DOCKER_IMAGE_CELERY_WORKER)"; \
		worker_remote="$$registry/$(DOCKER_IMAGE_CELERY_WORKER)"; \
		echo "Pushing $$worker_tag -> $$worker_remote"; \
		docker tag "$$worker_tag" "$$worker_remote"; \
		docker push "$$worker_remote"; \
		\
		beat_tag="$(DOCKER_IMAGE_CELERY_BEAT)"; \
		beat_remote="$$registry/$(DOCKER_IMAGE_CELERY_BEAT)"; \
		echo "Pushing $$beat_tag -> $$beat_remote"; \
		docker tag "$$beat_tag" "$$beat_remote"; \
		docker push "$$beat_remote"; \
	fi; \
	echo "Docker images published to $$registry"

run-docker: validate-all build-docker
	$(call log_section_start,Starting Docker Application)
	$(call show_build_config)
	@export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development); \
	export SCHEDULER=$(SCHEDULER); \
	export DOCKER_IMAGE_FRONTEND="coinmaker-frontend:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_BACKEND="coinmaker-backend:$(if $(filter release,$(MODE)),$(SCHEDULER),$(SCHEDULER)-debug)"; \
	export DOCKER_IMAGE_CELERY_WORKER="coinmaker-celery-worker:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_CELERY_BEAT="coinmaker-celery-beat:$(if $(filter release,$(MODE)),latest,debug)"; \
	compose_cmd="$(strip $(docker-compose-cmd))"; \
	$(call log_step,Running: $$compose_cmd up); \
	$(call log_info,Using images: Frontend=$$DOCKER_IMAGE_FRONTEND, Backend=$$DOCKER_IMAGE_BACKEND); \
	$(call log_info,Backend will be available on http://localhost:8000); \
	if [ "$(MODE)" = "debug" ]; then \
		$(call log_info,Frontend will be available on http://localhost:5173); \
	else \
		$(call log_info,Frontend will be available on http://localhost:3000); \
	fi; \
	if [ "$(SCHEDULER)" = "apscheduler" ]; then \
		$(call log_info,Task Queue: APScheduler (in-process)); \
	elif [ "$(SCHEDULER)" = "celery" ]; then \
		$(call log_info,Task Queue: Celery + Redis); \
	fi; \
	$$compose_cmd up

run-docker-detached: validate-all build-docker
	$(call log_section_start,Starting Docker Application (Detached Mode))
	$(call show_build_config)
	$(call log_step,Starting containers in detached mode)
	@export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development); \
	export SCHEDULER=$(SCHEDULER); \
	export DOCKER_IMAGE_FRONTEND="coinmaker-frontend:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_BACKEND="coinmaker-backend:$(if $(filter release,$(MODE)),$(SCHEDULER),$(SCHEDULER)-debug)"; \
	export DOCKER_IMAGE_CELERY_WORKER="coinmaker-celery-worker:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_CELERY_BEAT="coinmaker-celery-beat:$(if $(filter release,$(MODE)),latest,debug)"; \
	compose_cmd="$(strip $(docker-compose-cmd))"; \
	echo "Running: $$compose_cmd up -d"; \
	echo "Using images: Frontend=$$DOCKER_IMAGE_FRONTEND, Backend=$$DOCKER_IMAGE_BACKEND"; \
	$$compose_cmd up -d
	$(call log_info,Services started in background!)
	$(call log_info,View logs: make docker-logs)
	$(call log_info,Stop services: make stop-docker)

stop-docker: validate-mode validate-scheduler
	$(call log_target_start,Stopping Docker Containers)
	@export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development); \
	export SCHEDULER=$(SCHEDULER); \
	export DOCKER_IMAGE_FRONTEND="coinmaker-frontend:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_BACKEND="coinmaker-backend:$(if $(filter release,$(MODE)),$(SCHEDULER),$(SCHEDULER)-debug)"; \
	export DOCKER_IMAGE_CELERY_WORKER="coinmaker-celery-worker:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_CELERY_BEAT="coinmaker-celery-beat:$(if $(filter release,$(MODE)),latest,debug)"; \
	compose_cmd="$(strip $(docker-compose-cmd))"; \
	$$compose_cmd down

docker-logs: validate-mode validate-scheduler
	@export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development); \
	export SCHEDULER=$(SCHEDULER); \
	export DOCKER_IMAGE_FRONTEND="coinmaker-frontend:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_BACKEND="coinmaker-backend:$(if $(filter release,$(MODE)),$(SCHEDULER),$(SCHEDULER)-debug)"; \
	export DOCKER_IMAGE_CELERY_WORKER="coinmaker-celery-worker:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_CELERY_BEAT="coinmaker-celery-beat:$(if $(filter release,$(MODE)),latest,debug)"; \
	compose_cmd="$(strip $(docker-compose-cmd))"; \
	if [ "$(SERVICE)" != "" ]; then \
		$$compose_cmd logs -f $(SERVICE); \
	else \
		$$compose_cmd logs -f; \
	fi

docker-status: validate-mode validate-scheduler
	$(call log_section_start,Docker Status ($(MODE) mode, $(SCHEDULER) scheduler))
	@export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development); \
	export SCHEDULER=$(SCHEDULER); \
	export DOCKER_IMAGE_FRONTEND="coinmaker-frontend:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_BACKEND="coinmaker-backend:$(if $(filter release,$(MODE)),$(SCHEDULER),$(SCHEDULER)-debug)"; \
	export DOCKER_IMAGE_CELERY_WORKER="coinmaker-celery-worker:$(if $(filter release,$(MODE)),latest,debug)"; \
	export DOCKER_IMAGE_CELERY_BEAT="coinmaker-celery-beat:$(if $(filter release,$(MODE)),latest,debug)"; \
	compose_cmd="$(strip $(docker-compose-cmd))"; \
	$$compose_cmd ps

clean-docker:
	@if [ "$(MODE)" = "" ] && [ "$(SCHEDULER)" = "" ]; then \
		echo "Cleaning all Docker containers and images..."; \
		docker compose down --remove-orphans 2>/dev/null || true; \
		docker compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true; \
		docker images --format "table {{.Repository}}:{{.Tag}}" | grep "coinmaker:" | xargs -r docker rmi 2>/dev/null || true; \
		echo "All Docker resources cleaned"; \
	else \
		if [ "$(MODE)" = "" ] || [ "$(SCHEDULER)" = "" ]; then \
			echo "Error: Both MODE and SCHEDULER must be specified for specific cleanup"; \
			echo "Usage: make clean-docker MODE=debug SCHEDULER=apscheduler"; \
			exit 1; \
		fi; \
		echo "Cleaning Docker resources ($(MODE) mode, $(SCHEDULER) scheduler)..."; \
		export ENVIRONMENT=$(if $(filter release,$(MODE)),production,development); \
		export SCHEDULER=$(SCHEDULER); \
		compose_cmd="$(strip $(docker-compose-cmd))"; \
		$$compose_cmd down --remove-orphans 2>/dev/null || true; \
		docker rmi "$(DOCKER_IMAGE_FRONTEND)" 2>/dev/null || true; \
		docker rmi "$(DOCKER_IMAGE_BACKEND)" 2>/dev/null || true; \
		if [ "$(SCHEDULER)" = "celery" ]; then \
			docker rmi "$(DOCKER_IMAGE_CELERY_WORKER)" 2>/dev/null || true; \
			docker rmi "$(DOCKER_IMAGE_CELERY_BEAT)" 2>/dev/null || true; \
		fi; \
		echo "Docker resources cleaned"; \
	fi
	$(call log_step,Cleaning up dangling images and volumes)
	@docker image prune -f
	@docker volume prune -f
	@docker network prune -f

_tag-frontend-image:
	$(call log_step,Tagging frontend Docker image)
	@docker tag "coin-maker-frontend:temp" "$(DOCKER_IMAGE_FRONTEND)"
	$(call log_info,Tagged coin-maker-frontend:temp -> $(DOCKER_IMAGE_FRONTEND))
	@if [ "$(MODE)" = "release" ]; then \
		docker tag "coin-maker-frontend:temp" "coinmaker-frontend:$(VERSION_MAJOR_ONLY)"; \
		echo "Tagged coin-maker-frontend:temp -> coinmaker-frontend:$(VERSION_MAJOR_ONLY)"; \
		docker tag "coin-maker-frontend:temp" "coinmaker-frontend:latest"; \
		echo "Tagged coin-maker-frontend:temp -> coinmaker-frontend:latest"; \
	else \
		docker tag "coin-maker-frontend:temp" "coinmaker-frontend:$(VERSION_MAJOR_ONLY)-debug"; \
		echo "Tagged coin-maker-frontend:temp -> coinmaker-frontend:$(VERSION_MAJOR_ONLY)-debug"; \
		docker tag "coin-maker-frontend:temp" "coinmaker-frontend:debug"; \
		echo "Tagged coin-maker-frontend:temp -> coinmaker-frontend:debug"; \
	fi
	@docker rmi "coin-maker-frontend:temp" 2>/dev/null || true

_tag-backend-images:
	$(call log_step,Tagging backend Docker image)
	@docker tag "coin-maker-backend:temp" "$(DOCKER_IMAGE_BACKEND)"
	$(call log_info,Tagged coin-maker-backend:temp -> $(DOCKER_IMAGE_BACKEND))
	@if [ "$(MODE)" = "release" ]; then \
		docker tag "coin-maker-backend:temp" "coinmaker-backend:$(VERSION_MAJOR_ONLY)-$(SCHEDULER)"; \
		echo "Tagged coin-maker-backend:temp -> coinmaker-backend:$(VERSION_MAJOR_ONLY)-$(SCHEDULER)"; \
		docker tag "coin-maker-backend:temp" "coinmaker-backend:$(SCHEDULER)"; \
		echo "Tagged coin-maker-backend:temp -> coinmaker-backend:$(SCHEDULER)"; \
		if [ "$(SCHEDULER)" = "apscheduler" ]; then \
			docker tag "coin-maker-backend:temp" "coinmaker-backend:latest"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-backend:latest (default)"; \
		fi; \
	else \
		docker tag "coin-maker-backend:temp" "coinmaker-backend:$(VERSION_MAJOR_ONLY)-$(SCHEDULER)-debug"; \
		echo "Tagged coin-maker-backend:temp -> coinmaker-backend:$(VERSION_MAJOR_ONLY)-$(SCHEDULER)-debug"; \
		docker tag "coin-maker-backend:temp" "coinmaker-backend:$(SCHEDULER)-debug"; \
		echo "Tagged coin-maker-backend:temp -> coinmaker-backend:$(SCHEDULER)-debug"; \
	fi
	@if [ "$(SCHEDULER)" = "celery" ]; then \
		docker tag "coin-maker-backend:temp" "$(DOCKER_IMAGE_CELERY_WORKER)"; \
		echo "Tagged coin-maker-backend:temp -> $(DOCKER_IMAGE_CELERY_WORKER)"; \
		docker tag "coin-maker-backend:temp" "$(DOCKER_IMAGE_CELERY_BEAT)"; \
		echo "Tagged coin-maker-backend:temp -> $(DOCKER_IMAGE_CELERY_BEAT)"; \
		if [ "$(MODE)" = "release" ]; then \
			docker tag "coin-maker-backend:temp" "coinmaker-celery-worker:$(VERSION_MAJOR_ONLY)"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-celery-worker:$(VERSION_MAJOR_ONLY)"; \
			docker tag "coin-maker-backend:temp" "coinmaker-celery-beat:$(VERSION_MAJOR_ONLY)"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-celery-beat:$(VERSION_MAJOR_ONLY)"; \
			docker tag "coin-maker-backend:temp" "coinmaker-celery-worker:latest"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-celery-worker:latest"; \
			docker tag "coin-maker-backend:temp" "coinmaker-celery-beat:latest"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-celery-beat:latest"; \
		else \
			docker tag "coin-maker-backend:temp" "coinmaker-celery-worker:$(VERSION_MAJOR_ONLY)-debug"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-celery-worker:$(VERSION_MAJOR_ONLY)-debug"; \
			docker tag "coin-maker-backend:temp" "coinmaker-celery-beat:$(VERSION_MAJOR_ONLY)-debug"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-celery-beat:$(VERSION_MAJOR_ONLY)-debug"; \
			docker tag "coin-maker-backend:temp" "coinmaker-celery-worker:debug"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-celery-worker:debug"; \
			docker tag "coin-maker-backend:temp" "coinmaker-celery-beat:debug"; \
			echo "Tagged coin-maker-backend:temp -> coinmaker-celery-beat:debug"; \
		fi; \
	fi
	@docker rmi "coin-maker-backend:temp" 2>/dev/null || true

.PHONY: build-frontend-docker build-backend-docker build-docker publish-docker run-docker run-docker-detached stop-docker docker-logs docker-status clean-docker _tag-frontend-image _tag-backend-images