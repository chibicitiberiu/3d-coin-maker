# Desktop Application Management
# Handles desktop app building and running

# Run desktop app in development mode
run-desktop mode="dev":
    #!/usr/bin/env bash
    set -e
    echo "Starting Coin Maker Desktop ({{mode}} mode)"
    
    # Build HMM dependency
    just build-hmm
    
    # Install dependencies if needed
    just install-deps
    
    # Start the desktop application
    cd backend
    # Add build directory to PATH so HMM binary can be found
    export PATH="$(pwd)/../build${PATH:+:${PATH}}"
    if [ "{{mode}}" = "dev" ]; then
        poetry run python desktop_main.py
    else
        poetry run python desktop_main.py --prod
    fi

# Build everything needed for desktop app
build-desktop mode="dev":
    #!/usr/bin/env bash
    set -e
    echo "Building desktop app ({{mode}} mode)..."
    
    # Build dependencies
    just build-hmm
    just install-deps
    
    # Use desktop frontend build for desktop app, otherwise respect mode
    if [ "{{mode}}" = "dev" ] || [ "{{mode}}" = "prod" ]; then
        just build-frontend desktop
    else
        just build-frontend {{mode}}
    fi
    
    echo "Desktop build complete"