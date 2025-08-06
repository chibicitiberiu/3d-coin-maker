# Runtime Commands
# Commands to run different variants of the application with proper dependency management

# Import all build modules
import "deps.just"
import "frontend.just"
import "backend.just"
import "desktop-artifacts.just"
import "docker.just"

# Run desktop application via development script (fastest for development)
run-desktop-local mode="debug":
    #!/usr/bin/env bash
    set -e
    
    # Validate parameters
    if [[ "{{mode}}" != "debug" && "{{mode}}" != "release" ]]; then
        echo "Error: mode must be 'debug' or 'release', got '{{mode}}'"
        exit 1
    fi
    
    echo "Starting Coin Maker Desktop ({{mode}} mode via development script)"
    
    # Ensure all dependencies are built
    just build-deps
    just install-deps
    just build-frontend mode="{{mode}}" variant="desktop"
    just build-backend mode="{{mode}}" variant="desktop" scheduler="apscheduler"
    
    # Start the desktop application via script
    cd backend
    # Add build directory to PATH so HMM binary can be found
    export PATH="$(pwd)/../build:$(pwd)/../build/external/hmm${PATH:+:${PATH}}"
    
    if [ "{{mode}}" = "debug" ]; then
        poetry run python desktop_main.py
    else
        poetry run python desktop_main.py --prod
    fi

# Run desktop application binary directly (tests the actual built binary)
run-desktop mode="release":
    #!/usr/bin/env bash
    set -e
    
    # Validate parameters
    if [[ "{{mode}}" != "debug" && "{{mode}}" != "release" ]]; then
        echo "Error: mode must be 'debug' or 'release', got '{{mode}}'"
        exit 1
    fi
    
    echo "Running desktop binary ({{mode}} mode)"
    
    # Ensure desktop binary is built
    just build-desktop mode="{{mode}}"
    
    # Find the binary in the build directory
    build_dir="build/desktop_{{mode}}_apscheduler"
    binary_path="$build_dir/backend/desktop_main.py"
    
    if [ ! -f "$binary_path" ]; then
        echo "Error: Desktop binary not found at $binary_path"
        echo "Make sure to run 'just build-desktop mode=\"{{mode}}\"' first"
        exit 1
    fi
    
    # Run the binary
    cd "$build_dir/backend"
    export PATH="$(pwd)/../../external/hmm:$(pwd)/../../build${PATH:+:${PATH}}"
    
    if [ "{{mode}}" = "debug" ]; then
        python desktop_main.py
    else
        python desktop_main.py --prod
    fi

# Run desktop AppImage
run-desktop-appimage:
    #!/usr/bin/env bash
    set -e
    echo "Running desktop AppImage..."
    
    appimage_path="build/artifacts/CoinMaker-$(arch).AppImage"
    
    if [ ! -f "$appimage_path" ]; then
        echo "Error: AppImage not found at $appimage_path"
        echo "Build it first with: just build-desktop-appimage mode=\"release\""
        exit 1
    fi
    
    echo "Starting $appimage_path"
    "$appimage_path"

# Run desktop Flatpak
run-desktop-flatpak:
    #!/usr/bin/env bash
    set -e
    echo "Running desktop Flatpak..."
    
    if ! flatpak list | grep -q "io.github.coinmaker.CoinMaker"; then
        echo "Error: Flatpak not installed"
        echo "Install it first with: just install-desktop-flatpak"
        exit 1
    fi
    
    echo "Starting Flatpak application..."
    flatpak run io.github.coinmaker.CoinMaker

# Run web application locally (development server)
run-web-local mode="debug" scheduler="apscheduler":
    #!/usr/bin/env bash
    set -e
    
    # Validate parameters
    if [[ "{{mode}}" != "debug" && "{{mode}}" != "release" ]]; then
        echo "Error: mode must be 'debug' or 'release', got '{{mode}}'"
        exit 1
    fi
    
    if [[ "{{scheduler}}" != "apscheduler" && "{{scheduler}}" != "celery" ]]; then
        echo "Error: scheduler must be 'apscheduler' or 'celery', got '{{scheduler}}'"
        exit 1
    fi
    
    echo "Starting web application locally ({{mode}} mode, {{scheduler}} scheduler)"
    
    # Ensure all dependencies are built
    just build-deps
    just install-deps
    just build-frontend mode="{{mode}}" variant="web"
    just build-backend mode="{{mode}}" variant="web" scheduler="{{scheduler}}"
    
    # Set environment variables
    export ENVIRONMENT="development"
    if [ "{{mode}}" = "release" ]; then
        export ENVIRONMENT="production"
    fi
    export SCHEDULER="{{scheduler}}"
    export VARIANT="web"
    export PATH="$(pwd)/build:$(pwd)/build/external/hmm${PATH:+:${PATH}}"
    
    # Start the web application
    cd backend
    
    if [ "{{scheduler}}" = "celery" ]; then
        echo "Note: Running with Celery scheduler requires Redis to be running"
        echo "Consider using Docker mode for full Celery setup"
    fi
    
    # Use the appropriate main file
    if [ -f "web_main.py" ]; then
        poetry run python web_main.py
    else
        poetry run python fastapi_main.py
    fi

# Run web application via Docker
run-web-docker mode="debug" scheduler="apscheduler":
    #!/usr/bin/env bash
    set -e
    
    # Validate parameters
    if [[ "{{mode}}" != "debug" && "{{mode}}" != "release" ]]; then
        echo "Error: mode must be 'debug' or 'release', got '{{mode}}'"
        exit 1
    fi
    
    if [[ "{{scheduler}}" != "apscheduler" && "{{scheduler}}" != "celery" ]]; then
        echo "Error: scheduler must be 'apscheduler' or 'celery', got '{{scheduler}}'"
        exit 1
    fi
    
    echo "Starting web application via Docker ({{mode}} mode, {{scheduler}} scheduler)"
    
    # Ensure Docker images are built
    just build-web-docker mode="{{mode}}" scheduler="{{scheduler}}"
    
    # Set environment variable
    if [ "{{mode}}" = "release" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Get compose command and start containers
    compose_cmd=$(just -f build-scripts/docker.just _docker-compose-cmd "{{mode}}" "{{scheduler}}")
    
    echo "Starting containers with: $compose_cmd up -d"
    $compose_cmd up -d
    
    echo ""
    echo "Services started in background!"
    if [ "{{mode}}" = "debug" ]; then
        echo "Backend available: http://localhost:8000"
        echo "Frontend available: http://localhost:5173"
    else
        echo "Application available: http://localhost:3000"
    fi
    
    if [ "{{scheduler}}" = "apscheduler" ]; then
        echo "Task Queue: APScheduler (in-process)"
    else
        echo "Task Queue: Celery + Redis"
    fi
    
    echo ""
    echo "View logs: just logs-web-docker mode=\"{{mode}}\" scheduler=\"{{scheduler}}\""
    echo "Stop services: just stop-web-docker mode=\"{{mode}}\" scheduler=\"{{scheduler}}\""

# Stop web Docker containers
stop-web-docker mode="debug" scheduler="apscheduler":
    #!/usr/bin/env bash
    set -e
    
    echo "Stopping web Docker containers ({{mode}} mode, {{scheduler}} scheduler)"
    
    # Set environment variable
    if [ "{{mode}}" = "release" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Get compose command and stop containers
    compose_cmd=$(just -f build-scripts/docker.just _docker-compose-cmd "{{mode}}" "{{scheduler}}")
    
    echo "Stopping containers with: $compose_cmd down"
    $compose_cmd down

# View Docker container logs
logs-web-docker mode="debug" scheduler="apscheduler" service="":
    #!/usr/bin/env bash
    set -e
    
    # Set environment variable
    if [ "{{mode}}" = "release" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Get compose command
    compose_cmd=$(just -f build-scripts/docker.just _docker-compose-cmd "{{mode}}" "{{scheduler}}")
    
    if [ "{{service}}" != "" ]; then
        echo "Viewing logs for service: {{service}}"
        $compose_cmd logs -f {{service}}
    else
        echo "Viewing logs for all services ({{mode}} mode, {{scheduler}} scheduler)"
        $compose_cmd logs -f
    fi

# Show Docker container status
status-web-docker mode="debug" scheduler="apscheduler":
    #!/usr/bin/env bash
    
    # Set environment variable
    if [ "{{mode}}" = "release" ]; then
        export ENVIRONMENT=production
    else
        export ENVIRONMENT=development
    fi
    
    # Get compose command
    compose_cmd=$(just -f build-scripts/docker.just _docker-compose-cmd "{{mode}}" "{{scheduler}}")
    
    echo "Docker Status ({{mode}} mode, {{scheduler}} scheduler):"
    echo "=============================="
    $compose_cmd ps