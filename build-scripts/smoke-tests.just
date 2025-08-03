# Smoke Tests
# Comprehensive end-to-end testing for all deployment configurations
# Tests run with VISIBLE browsers by default so you can watch the automation
#
# Usage Examples:
#   just smoke-test chrome                    # Run all tests with visible Chrome
#   just smoke-test firefox "Docker"         # Run Docker tests with visible Firefox  
#   just smoke-test-headless chrome          # Run with hidden browser
#   just smoke-test-config "Docker APScheduler (Development)" chrome
#
# Prerequisites: Run 'just smoke-test-install' first to set up WebDrivers

# List available smoke test configurations
smoke-test-list:
    #!/usr/bin/env bash
    echo "Available Smoke Test Configurations:"
    cd tests/smoke && python -m cli --list

# Run all available smoke tests with visible browser (usage: just smoke-test <browser> [filter])
smoke-test browser="chrome" filter="":
    #!/usr/bin/env bash
    echo "Running smoke tests..."
    echo "Browser: {{browser}}"
    if [ "{{filter}}" != "" ]; then
        echo "Filter: {{filter}}"
    fi
    
    cd tests/smoke
    
    # Build command
    cmd="python -m cli --browser {{browser}}"
    if [ "{{filter}}" != "" ]; then
        cmd="$cmd --config '{{filter}}'"
    fi
    
    echo "Command: $cmd"
    eval $cmd

# Run smoke tests in headless mode (usage: just smoke-test-headless <browser> [filter])
smoke-test-headless browser="chrome" filter="":
    #!/usr/bin/env bash
    echo "Running smoke tests in headless mode..."
    
    cd tests/smoke
    
    cmd="python -m cli --browser {{browser}} --headless"
    if [ "{{filter}}" != "" ]; then
        cmd="$cmd --config '{{filter}}'"
    fi
    
    eval $cmd

# Run smoke tests for specific configuration (usage: just smoke-test-config "<config>" <browser>)
smoke-test-config config browser="chrome":
    #!/usr/bin/env bash
    echo "Running smoke test for: {{config}}"
    cd tests/smoke && python -m cli --browser {{browser}} --config "{{config}}"

# Run smoke tests for web configurations only (usage: just smoke-test-web <browser>)
smoke-test-web browser="chrome":
    #!/usr/bin/env bash
    echo "Running smoke tests for web configurations..."
    cd tests/smoke && python -m cli --browser {{browser}} --config "web"

# Run smoke tests for Docker configurations only (usage: just smoke-test-docker <browser>)
smoke-test-docker browser="chrome":
    #!/usr/bin/env bash
    echo "Running smoke tests for Docker configurations..."
    cd tests/smoke && python -m cli --browser {{browser}} --config "docker"

# Run smoke tests for desktop configurations only (usage: just smoke-test-desktop <browser>)
smoke-test-desktop browser="chrome":
    #!/usr/bin/env bash
    echo "Running smoke tests for desktop configurations..."
    cd tests/smoke && python -m cli --browser {{browser}} --config "desktop"

# Run smoke tests using pytest (usage: just smoke-test-pytest <browser> <visible>)
smoke-test-pytest browser="chrome" visible="false":
    #!/usr/bin/env bash
    echo "Running smoke tests with pytest..."
    
    # Set pytest arguments
    args="--browser={{browser}}"
    if [ "{{visible}}" = "false" ]; then
        args="$args --headless"
    fi
    
    # Run pytest
    cd tests/smoke && pytest test_smoke.py -v $args

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
            # Get Chrome version and determine ChromeDriver version
            if command -v google-chrome &> /dev/null; then
                CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
            elif command -v chromium-browser &> /dev/null; then
                CHROME_VERSION=$(chromium-browser --version | grep -oP '\d+\.\d+\.\d+')
            elif command -v chromium &> /dev/null; then
                CHROME_VERSION=$(chromium --version | grep -oP '\d+\.\d+\.\d+')
            fi
            
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

# Quick smoke test - just test one configuration
smoke-test-quick:
    #!/usr/bin/env bash
    echo "Quick smoke test - testing first available configuration..."
    cd tests/smoke && python3 quick_test.py

# Check smoke test requirements
smoke-test-check:
    #!/usr/bin/env bash
    echo "Checking smoke test requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python 3 not found"
        exit 1
    fi
    echo "Python 3 available"
    
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
    echo "Python packages available"
    
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
    echo "Browsers available: ${browsers[*]}"
    
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
    echo "WebDrivers available: ${drivers[*]}"
    
    echo "All smoke test requirements satisfied!"