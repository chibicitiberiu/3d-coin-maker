# Dependencies Management
# Handles HMM, GLM, and project dependencies

# Configuration
hmm_dir := "build/external/hmm"

# Clone and build the HMM library
build-hmm:
    #!/usr/bin/env bash
    set -e
    echo "Building HMM library..."
    
    # Create build and external directories
    mkdir -p build/external
    
    # Check GLM dependency
    echo "Checking GLM dependency..."
    if [ -f "/usr/include/glm/glm.hpp" ] || [ -f "/usr/local/include/glm/glm.hpp" ]; then
        echo "GLM headers found"
    else
        echo "Installing GLM dependency..."
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y libglm-dev
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf install -y glm-devel
        elif command -v pacman &> /dev/null; then
            # Arch Linux
            sudo pacman -S --noconfirm glm
        else
            echo "Error: Could not auto-install GLM. Please install libglm-dev/glm-devel manually."
            echo "Ubuntu/Debian: sudo apt-get install libglm-dev"
            echo "Fedora: sudo dnf install glm-devel"
            echo "Arch: sudo pacman -S glm"
            exit 1
        fi
    fi
    
    # Clone HMM if not exists
    if [ ! -d "{{hmm_dir}}" ]; then
        echo "Cloning HMM library..."
        git clone https://github.com/fogleman/hmm.git {{hmm_dir}}
    else
        echo "HMM directory exists, pulling latest..."
        cd {{hmm_dir}}
        git pull
        cd ../..
    fi
    
    # Build HMM
    cd {{hmm_dir}}
    if [ ! -f "Makefile" ]; then
        echo "Error: No Makefile found in HMM directory"
        exit 1
    fi
    
    echo "Compiling HMM..."
    make clean || true
    make
    
    # Ensure binary is executable and accessible
    if [ -f "hmm" ]; then
        chmod +x hmm
        echo "HMM built successfully: $(pwd)/hmm"
        
        # Create symlink in build directory for easy access
        cd ../../..
        ln -sf external/hmm/hmm build/hmm
        echo "Created symlink: build/hmm -> external/hmm/hmm"
    else
        echo "Error: HMM build failed - binary not found"
        exit 1
    fi

# Install all project dependencies
install-deps:
    #!/usr/bin/env bash
    set -e
    echo "Installing dependencies..."
    
    # Backend dependencies
    echo "Installing backend dependencies..."
    cd backend
    poetry install
    cd ..
    
    # Frontend dependencies
    echo "Installing frontend dependencies..."
    cd frontend
    pnpm install
    cd ..
    
    echo "All dependencies installed"

# Check system dependencies
check-deps:
    #!/usr/bin/env bash
    set -e
    echo "Checking system dependencies..."
    
    # Check required tools
    commands=("poetry" "pnpm" "git" "make" "gcc" "python3")
    
    for cmd in "${commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            echo "OK: $cmd"
        else
            echo "MISSING: $cmd"
        fi
    done
    
    # Check GLM headers
    if [ -f "/usr/include/glm/glm.hpp" ] || [ -f "/usr/local/include/glm/glm.hpp" ]; then
        echo "OK: GLM headers"
    else
        echo "MISSING: GLM headers (libglm-dev/glm-devel)"
    fi
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "Python: $python_version"
    
    # Check Node version
    if command -v node &> /dev/null; then
        node_version=$(node --version)
        echo "Node: $node_version"
    fi
    
    # Check platform
    echo "Platform: $(uname -s) $(uname -m)"