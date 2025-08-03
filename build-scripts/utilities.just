# Utility Commands
# Development tools and maintenance tasks

# Clean build artifacts
clean:
    #!/usr/bin/env bash
    set -e
    echo "Cleaning build artifacts..."
    
    # Clean all build artifacts (frontend, node_modules, .svelte-kit, etc.)
    rm -rf build/*
    
    # Clean backend Python cache (in build directory)
    rm -rf backend/__pycache__
    find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    rm -rf backend/dist
    rm -rf backend/build
    
    # Clean AppImage build
    rm -rf build/appimage
    rm -f build/*.AppImage
    
    # Clean HMM build (optional)
    if [ -d "build/external/hmm" ]; then
        cd build/external/hmm
        make clean || true
        cd ../../..
    fi
    
    # Clean temporary files
    rm -rf temp/*
    rm -rf backend/temp/*
    
    # Remove symlinks
    rm -f hmm
    
    echo "Clean complete"

# Run tests
test:
    #!/usr/bin/env bash
    set -e
    echo "Running tests..."
    
    # Backend tests
    cd backend
    poetry run pytest
    cd ..
    
    # Frontend tests (if any)
    cd frontend
    if [ -f "package.json" ] && grep -q "test" package.json; then
        pnpm test
    fi
    cd ..

# Format code
format:
    #!/usr/bin/env bash
    set -e
    echo "Formatting code..."
    
    # Backend
    cd backend
    poetry run ruff format .
    cd ..
    
    # Frontend
    cd frontend
    if command -v prettier &> /dev/null; then
        prettier --write src/
    fi
    cd ..

# Lint code  
lint:
    #!/usr/bin/env bash
    set -e
    echo "Linting code..."
    
    # Backend
    cd backend
    poetry run ruff check .
    poetry run pyright .
    cd ..
    
    # Frontend
    cd frontend
    if grep -q "lint" package.json; then
        pnpm run lint
    fi
    cd ..

# Type check code
typecheck:
    #!/usr/bin/env bash
    set -e
    echo "Type checking code..."
    
    # Backend
    cd backend
    poetry run pyright .
    cd ..
    
    # Frontend
    cd frontend
    if grep -q "check" package.json; then
        pnpm run check
    fi
    cd ..

# Security audit
audit:
    #!/usr/bin/env bash
    set -e
    echo "Running security audit..."
    
    # Backend (if safety is installed)
    cd backend
    if poetry run safety --version &> /dev/null; then
        poetry run safety check
    else
        echo "Safety not installed for Python audit"
    fi
    cd ..
    
    # Frontend
    cd frontend
    pnpm audit
    cd ..