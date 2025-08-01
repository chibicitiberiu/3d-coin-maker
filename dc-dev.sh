#!/bin/bash

# Docker Compose development wrapper script
# Usage: ./dc-dev.sh <command> [args...]
#
# Special shortcuts:
#   run     - build and up -d (with optional service names)
#   restart - build and restart (with optional service names) 
#   recreate - stop, rm, build, and up -d (with optional service names)
#
# All other commands are passed directly to docker compose

COMPOSE_FILE="docker-compose.dev.yml"
DOCKER_COMPOSE="docker compose -f $COMPOSE_FILE"

# Colors for our output (different from Docker's typical colors)
CYAN='\033[0;36m'
BOLD_CYAN='\033[1;36m'
NC='\033[0m' # No Color

# Function to print our status messages
print_status() {
    echo -e "${BOLD_CYAN}[$1]${NC}"
}

# Function to show usage
show_usage() {
    echo "Docker Compose Development Wrapper"
    echo ""
    echo "Usage: ./dc-dev.sh <command> [args...]"
    echo ""
    echo "Special shortcuts:"
    echo "  run [services...]     - Build and start services in detached mode"
    echo "  restart [services...] - Build and restart services"
    echo "  recreate [services...] - Stop, remove, build, and start services"
    echo ""
    echo "Standard docker compose commands:"
    echo "  up, down, build, logs, ps, exec, etc."
    echo ""
    echo "Examples:"
    echo "  ./dc-dev.sh run                    # Build and start all services"
    echo "  ./dc-dev.sh run backend frontend   # Build and start specific services"
    echo "  ./dc-dev.sh restart backend        # Build and restart backend service"
    echo "  ./dc-dev.sh recreate               # Full recreation of all services"
    echo "  ./dc-dev.sh logs -f backend        # Follow backend logs"
    echo "  ./dc-dev.sh ps                     # Show running services"
}

# Check if no arguments provided
if [ $# -eq 0 ]; then
    show_usage
    exit 1
fi

COMMAND=$1
shift  # Remove first argument, rest will be passed as additional args

case "$COMMAND" in
    "run")
        print_status "Building services..."
        $DOCKER_COMPOSE build
        if [ $? -eq 0 ]; then
            print_status "Starting services in detached mode..."
            echo "Backend will be available on http://localhost:8000"
            echo "Frontend will be available on http://localhost:5173"
            $DOCKER_COMPOSE up -d $@
        else
            print_status "Build failed, not starting services"
            exit 1
        fi
        ;;
    
    "restart")
        print_status "Building services..."
        $DOCKER_COMPOSE build
        if [ $? -eq 0 ]; then
            print_status "Restarting services..."
            $DOCKER_COMPOSE restart $@
        else
            print_status "Build failed, not restarting services"
            exit 1
        fi
        ;;
    
    "recreate")
        print_status "Stopping containers..."
        $DOCKER_COMPOSE stop
        print_status "Removing containers..."
        $DOCKER_COMPOSE rm -f
        print_status "Building services..."
        $DOCKER_COMPOSE build
        if [ $? -eq 0 ]; then
            print_status "Starting services in detached mode..."
            echo "Backend will be available on http://localhost:8000"
            echo "Frontend will be available on http://localhost:5173"
            $DOCKER_COMPOSE up -d $@
        else
            print_status "Build failed, not starting services"
            exit 1
        fi
        ;;
    
    "help"|"-h"|"--help")
        show_usage
        ;;
    
    *)
        # Pass all other commands directly to docker compose
        $DOCKER_COMPOSE "$COMMAND" $@
        ;;
esac