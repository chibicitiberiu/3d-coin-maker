# Docker Web Application Management
# Simplified Docker builds and container orchestration with proper dependency management
# Eliminates the 285-line duplication from the original docker.just

# Import dependencies
import "deps.just"
import "frontend.just" 
import "backend.just"

# Build Docker images for web deployment
# Usage: MODE=debug SCHEDULER=apscheduler just build-web-docker
build-web-docker:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters with defaults
    mode="${MODE:-debug}"
    scheduler="${SCHEDULER:-apscheduler}"
    
    # Validate parameters
    if [[ "$mode" != "debug" && "$mode" != "release" ]]; then
        echo "Error: MODE must be 'debug' or 'release', got '$mode'"
        exit 1
    fi
    
    if [[ "$scheduler" != "apscheduler" && "$scheduler" != "celery" ]]; then
        echo "Error: SCHEDULER must be 'apscheduler' or 'celery', got '$scheduler'"
        exit 1
    fi
    
    echo "Building Docker images ($mode mode, $scheduler scheduler)..."
    
    # Build component dependencies first
    just build-deps
    MODE="$mode" VARIANT="web" just build-frontend
    MODE="$mode" VARIANT="web" SCHEDULER="$scheduler" just build-backend
    
    # Set environment variables for Docker build
    export ENVIRONMENT="development"
    if [ "$mode" = "release" ]; then
        export ENVIRONMENT="production"
    fi
    
    export SCHEDULER="$scheduler"
    
    # Build Docker images using compose
    compose_cmd=$(MODE="$mode" SCHEDULER="$scheduler" just _docker-compose-cmd)
    
    echo "Building images with: $compose_cmd build"
    $compose_cmd build
    
    # Tag images with our naming convention
    MODE="$mode" SCHEDULER="$scheduler" just _tag-docker-images
    
    echo "Docker images built and tagged:"
    echo "  coinmaker:web_${mode}_${scheduler}"
    if [ "$scheduler" = "celery" ]; then
        echo "  coinmaker-celery:web_${mode}_${scheduler}"
    fi

# Publish Docker images to registry
# Usage: MODE=debug SCHEDULER=apscheduler REGISTRY=docker.io just publish-web-docker
publish-web-docker:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters with defaults
    mode="${MODE:-debug}"
    scheduler="${SCHEDULER:-apscheduler}"
    registry="${REGISTRY:-docker.io}"
    
    # Validate parameters
    if [[ "$mode" != "debug" && "$mode" != "release" ]]; then
        echo "Error: MODE must be 'debug' or 'release', got '$mode'"
        exit 1
    fi
    
    if [[ "$scheduler" != "apscheduler" && "$scheduler" != "celery" ]]; then
        echo "Error: SCHEDULER must be 'apscheduler' or 'celery', got '$scheduler'"
        exit 1
    fi
    
    echo "Publishing Docker images to $registry ($mode mode, $scheduler scheduler)..."
    
    # Ensure images are built
    MODE="$mode" SCHEDULER="$scheduler" just build-web-docker
    
    # Tag and push main image
    main_tag="coinmaker:web_${mode}_${scheduler}"
    remote_tag="$registry/coinmaker:web_${mode}_${scheduler}"
    
    echo "Pushing $main_tag -> $remote_tag"
    docker tag "$main_tag" "$remote_tag"
    docker push "$remote_tag"
    
    # Tag and push celery image if applicable
    if [ "$scheduler" = "celery" ]; then
        celery_tag="coinmaker-celery:web_${mode}_${scheduler}"
        celery_remote_tag="$registry/coinmaker-celery:web_${mode}_${scheduler}"
        
        echo "Pushing $celery_tag -> $celery_remote_tag"
        docker tag "$celery_tag" "$celery_remote_tag"
        docker push "$celery_remote_tag"
    fi
    
    echo "Docker images published to $registry"

# Clean Docker images and containers
# Usage: MODE=debug SCHEDULER=apscheduler just clean-web-docker (or just clean-web-docker for all)
clean-web-docker:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters (empty means clean all)
    mode="${MODE:-}"
    scheduler="${SCHEDULER:-}"
    
    if [ "$mode" = "" ] && [ "$scheduler" = "" ]; then
        echo "Cleaning all Docker containers and images..."
        
        # Stop all running containers for this project
        docker compose down --remove-orphans 2>/dev/null || true
        docker compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
        
        # Remove project-specific images
        docker images --format "table {{{{.Repository}}}}:{{{{.Tag}}}}" | grep "coinmaker:" | xargs -r docker rmi || true
        
        echo "All Docker resources cleaned"
    else
        if [ "$mode" = "" ] || [ "$scheduler" = "" ]; then
            echo "Error: Both MODE and SCHEDULER must be specified for specific cleanup"
            exit 1
        fi
        
        echo "Cleaning Docker resources ($mode mode, $scheduler scheduler)..."
        
        # Stop specific containers
        compose_cmd=$(MODE="$mode" SCHEDULER="$scheduler" just _docker-compose-cmd)
        $compose_cmd down --remove-orphans 2>/dev/null || true
        
        # Remove specific images
        docker rmi "coinmaker:web_${mode}_${scheduler}" 2>/dev/null || true
        if [ "$scheduler" = "celery" ]; then
            docker rmi "coinmaker-celery:web_${mode}_${scheduler}" 2>/dev/null || true
        fi
        
        echo "Docker resources cleaned"
    fi
    
    # Clean up dangling images and volumes
    docker image prune -f
    docker volume prune -f
    docker network prune -f

# Helper: Build docker-compose command for given mode and scheduler
_docker-compose-cmd:
    #!/usr/bin/env bash
    
    # Get parameters with defaults
    mode="${MODE:-debug}"
    scheduler="${SCHEDULER:-apscheduler}"
    
    # Set environment variable
    if [ "$mode" = "release" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Build compose command based on mode and scheduler
    if [ "$mode" = "debug" ]; then
        # Development mode - uses docker-compose.yml + docker-compose.override.yml automatically
        compose_cmd="docker compose"
        
        if [ "$scheduler" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "$scheduler" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.yml -f docker-compose.apscheduler.yml"
        fi
    else
        # Production mode
        compose_cmd="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        
        if [ "$scheduler" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "$scheduler" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.apscheduler.yml"
        fi
    fi
    
    echo "$compose_cmd"

# Helper: Tag Docker images with our naming convention
_tag-docker-images:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters with defaults
    mode="${MODE:-debug}"
    scheduler="${SCHEDULER:-apscheduler}"
    
    # Get the project name (usually the directory name)
    project_name=$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')
    
    # Tag main backend image
    if docker images | grep -q "${project_name}[-_]backend"; then
        backend_image=$(docker images --format "table {{{{.Repository}}}}:{{{{.Tag}}}}" | grep "${project_name}[-_]backend" | head -1)
        docker tag "$backend_image" "coinmaker:web_${mode}_${scheduler}"
        echo "Tagged $backend_image -> coinmaker:web_${mode}_${scheduler}"
    fi
    
    # Tag celery image if it exists
    if [ "$scheduler" = "celery" ] && docker images | grep -q "${project_name}[-_]celery"; then
        celery_image=$(docker images --format "table {{{{.Repository}}}}:{{{{.Tag}}}}" | grep "${project_name}[-_]celery" | head -1)
        docker tag "$celery_image" "coinmaker-celery:web_${mode}_${scheduler}"
        echo "Tagged $celery_image -> coinmaker-celery:web_${mode}_${scheduler}"
    fi