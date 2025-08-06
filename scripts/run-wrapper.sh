#!/bin/bash
set -e

# Simplified run wrapper for Coin Maker
# Coordinates frontend and backend servers with minimal argument parsing

# Default values
DEBUG=false
SCHEDULER="apscheduler"
BACKEND_PORT="8001"
FRONTEND_TYPE="dev"  # "dev" or "preview"
ONLY_BACKEND=false
ONLY_FRONTEND=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            # Convert MODE to DEBUG flag
            if [[ "$2" == "debug" ]]; then
                DEBUG=true
            elif [[ "$2" == "release" ]]; then
                DEBUG=false
            else
                echo "Error: MODE must be 'debug' or 'release', got '$2'"
                exit 1
            fi
            shift 2
            ;;
        --scheduler)
            SCHEDULER="$2"
            if [[ "$SCHEDULER" != "apscheduler" && "$SCHEDULER" != "celery" ]]; then
                echo "Error: SCHEDULER must be 'apscheduler' or 'celery', got '$SCHEDULER'"
                exit 1
            fi
            shift 2
            ;;
        --backend-port)
            BACKEND_PORT="$2"
            shift 2
            ;;
        --frontend-type)
            FRONTEND_TYPE="$2"
            if [[ "$FRONTEND_TYPE" != "dev" && "$FRONTEND_TYPE" != "preview" ]]; then
                echo "Error: FRONTEND_TYPE must be 'dev' or 'preview', got '$FRONTEND_TYPE'"
                exit 1
            fi
            shift 2
            ;;
        --only-backend)
            ONLY_BACKEND=true
            shift
            ;;
        --only-frontend)
            ONLY_FRONTEND=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --mode MODE              debug|release (default: debug)"
            echo "  --scheduler SCHEDULER    apscheduler|celery (default: apscheduler)"
            echo "  --backend-port PORT      Backend port (default: 8001)"
            echo "  --frontend-type TYPE     dev|preview (default: dev)"
            echo "  --only-backend           Start only the backend server"
            echo "  --only-frontend          Start only the frontend server"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate mutual exclusion
if [[ "$ONLY_BACKEND" == "true" && "$ONLY_FRONTEND" == "true" ]]; then
    echo "Error: Cannot specify both --only-backend and --only-frontend"
    exit 1
fi

# Use environment variables from makefile, with fallback defaults
BACKEND_SRC="${BACKEND_SRC:-backend}"
FRONTEND_SRC="${FRONTEND_SRC:-frontend}"
BUILD_DIR="${BUILD_DIR:-build/$([ "$DEBUG" = "true" ] && echo "debug" || echo "release")}"

# Frontend configuration
if [[ "$FRONTEND_TYPE" = "dev" ]]; then
    FRONTEND_PORT="5173"
    FRONTEND_CMD="pnpm run dev"
else
    FRONTEND_PORT="4173"
    FRONTEND_CMD="pnpm run preview"
fi

# API URL for frontend
API_BASE_URL="http://localhost:${BACKEND_PORT}/api"

echo "Starting Coin Maker with configuration:"
echo "  Debug: $DEBUG"
echo "  Scheduler: $SCHEDULER"
echo "  Backend Port: $BACKEND_PORT"
if [[ "$ONLY_BACKEND" != "true" ]]; then
    echo "  Frontend Type: $FRONTEND_TYPE"
    echo "  Frontend Port: $FRONTEND_PORT"
fi
echo "  API Base URL: $API_BASE_URL"
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    # Kill all background jobs
    jobs -p | xargs -r kill
    wait
    echo "Shutdown complete"
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

# Start frontend server
if [[ "$ONLY_BACKEND" != "true" ]]; then
    echo "Starting frontend server..."
    (
        cd "$FRONTEND_SRC"
        MODE="$([ "$DEBUG" = "true" ] && echo "development" || echo "production")" \
        PUBLIC_API_BASE_URL="$API_BASE_URL" \
        BUILD_OUTPUT="../${BUILD_DIR}/frontend" \
        $FRONTEND_CMD
    ) &
    
    # Give frontend a moment to start
    sleep 2
fi

# Start backend server
if [[ "$ONLY_FRONTEND" != "true" ]]; then
    echo "Starting backend server..."
    
    # Check if backend build exists
    if [[ ! -f "${BUILD_DIR}/backend/venv/bin/python" ]]; then
        echo "Error: Backend build not found at ${BUILD_DIR}/backend/venv/bin/python"
        echo "Run 'make build-backend' first"
        exit 1
    fi
    
    # Start backend with main.py
    (
        cd "$BACKEND_SRC"
        "../${BUILD_DIR}/backend/venv/bin/python" main.py --run \
            $([ "$DEBUG" = "true" ] && echo "--debug") \
            --scheduler "$SCHEDULER" \
            --port "$BACKEND_PORT"
    ) &
fi

echo ""
echo "Coin Maker is running!"
if [[ "$ONLY_BACKEND" != "true" ]]; then
    echo "Frontend: http://localhost:$FRONTEND_PORT"
fi
if [[ "$ONLY_FRONTEND" != "true" ]]; then
    echo "Backend:  http://localhost:$BACKEND_PORT"
    echo "API Docs: http://localhost:$BACKEND_PORT/docs"
fi
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for background processes
wait