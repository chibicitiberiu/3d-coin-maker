# Frontend Build Management
# Handles different frontend build modes and configurations

# Build frontend for specified mode
build-frontend mode="dev":
    #!/usr/bin/env bash
    set -e
    echo "Building frontend ({{mode}} mode)..."
    
    # Create build directory
    mkdir -p build/frontend
    
    cd frontend
    pnpm install
    
    case "{{mode}}" in
        "dev"|"development")
            pnpm run build:dev
            ;;
        "prod"|"production")
            pnpm run build:prod
            ;;
        "desktop")
            pnpm run build:desktop
            ;;
        *)
            echo "Unknown mode: {{mode}}, using default build"
            pnpm run build
            ;;
    esac
    
    echo "Frontend build complete"

# Start frontend development server
dev-frontend:
    #!/usr/bin/env bash
    set -e
    echo "Starting frontend development server..."
    cd frontend
    pnpm run dev

# Preview frontend build
preview-frontend:
    #!/usr/bin/env bash
    set -e
    echo "Starting frontend preview server..."
    cd frontend
    pnpm run preview