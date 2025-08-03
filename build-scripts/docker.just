# Docker Container Management
# Handles Docker builds and container orchestration using the new unified structure

# Build and start Docker containers
run-docker mode="dev" profile="":
    #!/usr/bin/env bash
    set -e
    echo "Starting Docker containers ({{mode}} mode)"
    
    # Set and export environment variable properly
    if [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Build compose command based on mode and profile
    if [ "{{mode}}" = "dev" ] || [ "{{mode}}" = "development" ]; then
        # Development mode - uses docker-compose.yml + docker-compose.override.yml automatically
        compose_cmd="docker compose"
        
        # Add profile if specified
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.yml -f docker-compose.apscheduler.yml"
        fi
    elif [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        # Production mode
        compose_cmd="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        
        # Add profile if specified  
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.apscheduler.yml"
        fi
    else
        echo "Error: Invalid mode '{{mode}}'. Use 'dev' or 'prod'"
        exit 1
    fi
    
    # Execute the command
    echo "Running: $compose_cmd up --build"
    echo "Backend will be available on http://localhost:8000"
    if [ "{{mode}}" = "dev" ]; then
        echo "Frontend will be available on http://localhost:5173"
    else
        echo "Frontend will be available on http://localhost:3000"  
    fi
    
    if [ "{{profile}}" = "apscheduler" ]; then
        echo "Task Queue: APScheduler (in-process)"
    elif [ "{{profile}}" = "celery" ]; then
        echo "Task Queue: Celery + Redis"
    else
        echo "Task Queue: Backend only"
    fi
    
    $compose_cmd up --build

# Start containers in detached mode
run-docker-detached mode="dev" profile="":
    #!/usr/bin/env bash
    set -e
    echo "Starting Docker containers in detached mode ({{mode}} mode)"
    
    # Set and export environment variable properly
    if [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Build compose command (same logic as run-docker)
    if [ "{{mode}}" = "dev" ] || [ "{{mode}}" = "development" ]; then
        compose_cmd="docker compose"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.yml -f docker-compose.apscheduler.yml"
        fi
    elif [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        compose_cmd="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.apscheduler.yml"
        fi
    else
        echo "Error: Invalid mode '{{mode}}'. Use 'dev' or 'prod'"
        exit 1
    fi
    
    echo "Running: $compose_cmd up -d --build"
    $compose_cmd up -d --build
    
    echo ""
    echo "Services started in background!"
    echo "View logs: just docker-logs {{mode}} {{profile}}"
    echo "Stop services: just stop-docker {{mode}} {{profile}}"

# Stop Docker containers  
stop-docker mode="dev" profile="":
    #!/usr/bin/env bash
    set -e
    echo "Stopping Docker containers ({{mode}} mode)"
    
    # Set and export environment variable properly
    if [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Build compose command (same logic as run-docker)
    if [ "{{mode}}" = "dev" ] || [ "{{mode}}" = "development" ]; then
        compose_cmd="docker compose"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.yml -f docker-compose.apscheduler.yml"
        fi
    elif [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        compose_cmd="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.apscheduler.yml"
        fi
    fi
    
    $compose_cmd down

# View Docker container logs
docker-logs mode="dev" profile="" service="":
    #!/usr/bin/env bash
    set -e
    
    # Set and export environment variable properly
    if [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Build compose command (same logic as run-docker)
    if [ "{{mode}}" = "dev" ] || [ "{{mode}}" = "development" ]; then
        compose_cmd="docker compose"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.yml -f docker-compose.apscheduler.yml"
        fi
    elif [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        compose_cmd="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.apscheduler.yml"
        fi
    fi
    
    if [ "{{service}}" != "" ]; then
        $compose_cmd logs -f {{service}}
    else
        $compose_cmd logs -f
    fi

# Restart specific services
restart-docker mode="dev" profile="" service="":
    #!/usr/bin/env bash
    set -e
    echo "Restarting Docker services ({{mode}} mode)"
    
    # Set and export environment variable properly
    if [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Build compose command (same logic as run-docker)
    if [ "{{mode}}" = "dev" ] || [ "{{mode}}" = "development" ]; then
        compose_cmd="docker compose"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.yml -f docker-compose.apscheduler.yml"
        fi
    elif [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        compose_cmd="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.apscheduler.yml"
        fi
    fi
    
    $compose_cmd build {{service}}
    $compose_cmd restart {{service}}

# Clean Docker containers and images
clean-docker:
    #!/usr/bin/env bash
    set -e
    echo "Cleaning Docker containers and images..."
    
    # Stop all running containers for this project
    docker compose down --remove-orphans 2>/dev/null || true
    docker compose -f docker-compose.yml -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true
    
    # Remove project-specific containers and images
    echo "Removing project containers..."
    docker container prune -f
    
    # Clean up volumes and networks  
    echo "Cleaning volumes and networks..."
    docker volume prune -f
    docker network prune -f
    
    echo "Docker cleanup complete"

# Show Docker container status
docker-status mode="dev" profile="":
    #!/usr/bin/env bash
    # Set and export environment variable properly
    if [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Build compose command (same logic as run-docker)
    if [ "{{mode}}" = "dev" ] || [ "{{mode}}" = "development" ]; then
        compose_cmd="docker compose"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.yml -f docker-compose.apscheduler.yml"
        fi
    elif [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        compose_cmd="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.apscheduler.yml"
        fi
    fi
    
    echo "Docker Status ({{mode}} mode):"
    echo "=============================="
    $compose_cmd ps

# Test Docker configuration without starting
test-docker-config mode="dev" profile="":
    #!/usr/bin/env bash
    # Set and export environment variable properly
    if [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    echo "Testing Docker configuration ({{mode}} mode with ENVIRONMENT=$ENVIRONMENT)..."
    
    # Build compose command (same logic as run-docker)
    if [ "{{mode}}" = "dev" ] || [ "{{mode}}" = "development" ]; then
        compose_cmd="docker compose"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.yml -f docker-compose.apscheduler.yml"
        fi
    elif [ "{{mode}}" = "prod" ] || [ "{{mode}}" = "production" ]; then
        compose_cmd="docker compose -f docker-compose.yml -f docker-compose.prod.yml"
        if [ "{{profile}}" = "celery" ]; then
            compose_cmd="$compose_cmd --profile celery"
        elif [ "{{profile}}" = "apscheduler" ]; then
            compose_cmd="$compose_cmd -f docker-compose.apscheduler.yml"
        fi
    fi
    
    echo "Configuration test:"
    $compose_cmd config --quiet && echo "Configuration is valid" || echo "Configuration has errors"