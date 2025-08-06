# Enhanced Smoke Tests
# Comprehensive end-to-end testing for all deployment configurations
# Integrates with the new build system configuration options

# Import build modules for dependency management
import "deps.just"
import "frontend.just"
import "backend.just" 
import "desktop-artifacts.just"
import "docker.just"
import "run.just"

# Run smoke tests for specific configuration
smoke-test mode="debug" variant="web" scheduler="apscheduler" browser="chrome":
    #!/usr/bin/env bash
    set -e
    
    # Validate parameters
    if [[ "{{mode}}" != "debug" && "{{mode}}" != "release" ]]; then
        echo "Error: mode must be 'debug' or 'release', got '{{mode}}'"
        exit 1
    fi
    
    if [[ "{{variant}}" != "web" && "{{variant}}" != "desktop" ]]; then
        echo "Error: variant must be 'web' or 'desktop', got '{{variant}}'"
        exit 1
    fi
    
    if [[ "{{scheduler}}" != "apscheduler" && "{{scheduler}}" != "celery" ]]; then
        echo "Error: scheduler must be 'apscheduler' or 'celery', got '{{scheduler}}'"
        exit 1
    fi
    
    # Desktop variant can only use apscheduler
    if [ "{{variant}}" = "desktop" ] && [ "{{scheduler}}" != "apscheduler" ]; then
        echo "Error: desktop variant only supports apscheduler scheduler"
        exit 1
    fi
    
    if [[ "{{browser}}" != "chrome" && "{{browser}}" != "firefox" ]]; then
        echo "Error: browser must be 'chrome' or 'firefox', got '{{browser}}'"
        exit 1
    fi
    
    echo "Running smoke test: {{mode}} {{variant}} {{scheduler}} ({{browser}})"
    
    # Build the configuration being tested
    config_name="{{variant}}_{{mode}}_{{scheduler}}"
    echo "Building configuration: $config_name"
    
    if [ "{{variant}}" = "desktop" ]; then
        just build-desktop mode="{{mode}}"
    else
        just build-web-docker mode="{{mode}}" scheduler="{{scheduler}}"
    fi
    
    # Ensure smoke test dependencies are installed
    just smoke-test-check
    
    # Run the smoke test
    cd tests/smoke
    
    # Map our configuration to the smoke test format
    smoke_config="${config_name}"
    if [ "{{variant}}" = "desktop" ]; then
        smoke_config="Desktop ({{mode}})"
    else
        smoke_config="Docker {{scheduler}} ({{mode}})"
    fi
    
    echo "Running smoke test for configuration: $smoke_config"
    python -m cli --browser {{browser}} --config "$smoke_config"

# Run smoke tests for all web configurations
smoke-test-web browser="chrome":
    #!/usr/bin/env bash
    set -e
    echo "Running smoke tests for all web configurations..."
    
    # Test all web combinations
    configurations=(
        "debug web apscheduler"
        "release web apscheduler" 
        "debug web celery"
        "release web celery"
    )
    
    for config in "${configurations[@]}"; do
        read -r mode variant scheduler <<< "$config"
        echo ""
        echo "Testing: $mode $variant $scheduler"
        just smoke-test mode="$mode" variant="$variant" scheduler="$scheduler" browser="{{browser}}"
    done

# Run smoke tests for all desktop configurations  
smoke-test-desktop browser="chrome":
    #!/usr/bin/env bash
    set -e
    echo "Running smoke tests for all desktop configurations..."
    
    # Test desktop configurations (always apscheduler)
    configurations=(
        "debug desktop apscheduler"
        "release desktop apscheduler"
    )
    
    for config in "${configurations[@]}"; do
        read -r mode variant scheduler <<< "$config"
        echo ""
        echo "Testing: $mode $variant $scheduler"
        just smoke-test mode="$mode" variant="$variant" scheduler="$scheduler" browser="{{browser}}"
    done

# Run smoke tests for all configurations
smoke-test-all browser="chrome":
    #!/usr/bin/env bash
    set -e
    echo "Running smoke tests for ALL configurations..."
    
    echo "Testing web configurations..."
    just smoke-test-web browser="{{browser}}"
    
    echo ""
    echo "Testing desktop configurations..."
    just smoke-test-desktop browser="{{browser}}"
    
    echo ""
    echo "All smoke tests completed!"

# Quick smoke test - just test one representative configuration
smoke-test-quick browser="chrome":
    #!/usr/bin/env bash
    set -e
    echo "Quick smoke test - testing debug web apscheduler configuration..."
    just smoke-test mode="debug" variant="web" scheduler="apscheduler" browser="{{browser}}"

# Install smoke test dependencies
smoke-test-install:
    #!/usr/bin/env bash
    echo "Installing smoke test dependencies..."
    
    # Check if pip/pip3 is available
    if command -v pip3 &> /dev/null; then
        PIP=pip3
    elif command -v pip &> /dev/null; then
        PIP=pip
    else
        echo "ERROR: pip not found"
        exit 1
    fi
    
    # Install Python dependencies
    echo "Installing Python packages..."
    $PIP install selenium pytest requests psutil
    
    # Install WebDrivers to local directory
    echo "Installing WebDrivers..."
    
    # Create test drivers directory
    mkdir -p build/test-drivers
    
    # Download and install GeckoDriver (Firefox)
    if command -v firefox &> /dev/null; then
        echo "Installing GeckoDriver for Firefox..."
        GECKODRIVER_VERSION="v0.35.0"
        GECKODRIVER_URL="https://github.com/mozilla/geckodriver/releases/download/${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz"
        
        if [ ! -f "build/test-drivers/geckodriver" ]; then
            curl -L -o build/test-drivers/geckodriver.tar.gz "$GECKODRIVER_URL"
            tar -xzf build/test-drivers/geckodriver.tar.gz -C build/test-drivers/
            chmod +x build/test-drivers/geckodriver
            rm build/test-drivers/geckodriver.tar.gz
            echo "GeckoDriver installed"
        else
            echo "GeckoDriver already installed"
        fi
    else
        echo "WARNING: Firefox not found, skipping GeckoDriver"
    fi
    
    # Download and install ChromeDriver (Chrome/Chromium)
    if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null || command -v chromium &> /dev/null; then
        echo "Installing ChromeDriver for Chrome/Chromium..."
        
        if [ ! -f "build/test-drivers/chromedriver" ]; then
            # Use a stable ChromeDriver version
            CHROMEDRIVER_VERSION="131.0.6778.85"
            CHROMEDRIVER_URL="https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip"
            
            curl -L -o build/test-drivers/chromedriver.zip "$CHROMEDRIVER_URL"
            cd build/test-drivers
            unzip -o chromedriver.zip
            mv chromedriver-linux64/chromedriver .
            rm -rf chromedriver-linux64 chromedriver.zip
            chmod +x chromedriver
            cd ../..
            echo "ChromeDriver installed"
        else
            echo "ChromeDriver already installed"
        fi
    else
        echo "WARNING: Chrome/Chromium not found, skipping ChromeDriver"
    fi
    
    echo "Smoke test dependencies installed"
    echo "WebDrivers installed to: build/test-drivers/"

# Check smoke test requirements
smoke-test-check:
    #!/usr/bin/env bash
    echo "Checking smoke test requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python 3 not found"
        exit 1
    fi
    
    # Check required Python packages
    missing_packages=()
    
    for package in selenium pytest requests psutil; do
        if ! python3 -c "import $package" 2>/dev/null; then
            missing_packages+=($package)
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo "ERROR: Missing Python packages: ${missing_packages[*]}"
        echo "Run: just smoke-test-install"
        exit 1
    fi
    
    # Check browsers
    browsers=()
    if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null; then
        browsers+=("Chrome/Chromium")
    fi
    if command -v firefox &> /dev/null; then
        browsers+=("Firefox")
    fi
    
    if [ ${#browsers[@]} -eq 0 ]; then
        echo "ERROR: No supported browsers found (Chrome/Chromium or Firefox)"
        exit 1
    fi
    
    # Check WebDrivers (system and local)
    drivers=()
    if command -v chromedriver &> /dev/null || [ -f "build/test-drivers/chromedriver" ]; then
        drivers+=("ChromeDriver")
    fi
    if command -v geckodriver &> /dev/null || [ -f "build/test-drivers/geckodriver" ]; then
        drivers+=("GeckoDriver")
    fi
    
    if [ ${#drivers[@]} -eq 0 ]; then
        echo "ERROR: No WebDrivers found (system or local)"
        echo "Run: just smoke-test-install"
        exit 1
    fi
    
    echo "✓ All smoke test requirements satisfied!"
    echo "Available browsers: ${browsers[*]}"
    echo "Available drivers: ${drivers[*]}"

# List all available smoke test configurations
smoke-test-list:
    #!/usr/bin/env bash
    echo "Available Smoke Test Configurations"
    echo "==================================="
    echo ""
    echo "Desktop Configurations:"
    echo "  just smoke-test mode=\"debug\" variant=\"desktop\" scheduler=\"apscheduler\" browser=\"chrome\""
    echo "  just smoke-test mode=\"release\" variant=\"desktop\" scheduler=\"apscheduler\" browser=\"chrome\""
    echo ""
    echo "Web Configurations:"
    echo "  just smoke-test mode=\"debug\" variant=\"web\" scheduler=\"apscheduler\" browser=\"chrome\""
    echo "  just smoke-test mode=\"debug\" variant=\"web\" scheduler=\"celery\" browser=\"chrome\""
    echo "  just smoke-test mode=\"release\" variant=\"web\" scheduler=\"apscheduler\" browser=\"chrome\""
    echo "  just smoke-test mode=\"release\" variant=\"web\" scheduler=\"celery\" browser=\"chrome\""
    echo ""
    echo "Batch Commands:"
    echo "  just smoke-test-quick           # Test one representative config"
    echo "  just smoke-test-web             # Test all web configs"
    echo "  just smoke-test-desktop         # Test all desktop configs"
    echo "  just smoke-test-all             # Test ALL configs"
    echo ""
    echo "Available browsers: chrome, firefox"