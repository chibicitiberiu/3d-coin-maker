# Smoke Tests

Comprehensive end-to-end smoke tests for Coin Maker that verify all deployment configurations work correctly.

## Quick Start

**Tests run with VISIBLE browsers by default so you can watch the automation!**

```bash
# 1. Install WebDrivers and dependencies (one-time setup)
just smoke-test-install

# 2. Run all available smoke tests with visible Chrome
just smoke-test chrome

# 3. Run tests for specific deployment mode with visible browser
just smoke-test-docker chrome

# 4. Run specific configuration test
just smoke-test-config "Docker APScheduler (Development)" firefox

# 5. Run in headless mode (hidden) if needed
just smoke-test-headless chrome
```

## Usage

### Available Commands

| Command | Usage | Description |
|---------|--------|-------------|
| `just smoke-test-install` | One-time setup | Install WebDrivers and dependencies |
| `just smoke-test-list` | Show available configs | List all detected test configurations |
| `just smoke-test <browser>` | `just smoke-test chrome` | Run all tests with **visible** browser |
| `just smoke-test <browser> "<filter>"` | `just smoke-test firefox "Docker"` | Run filtered tests with **visible** browser |
| `just smoke-test-headless <browser>` | `just smoke-test-headless chrome` | Run with hidden browser |
| `just smoke-test-config "<config>" <browser>` | `just smoke-test-config "Docker APScheduler (Development)" chrome` | Run specific configuration |
| `just smoke-test-docker <browser>` | `just smoke-test-docker firefox` | Run Docker tests only |
| `just smoke-test-web <browser>` | `just smoke-test-web chrome` | Run web server tests only |
| `just smoke-test-desktop <browser>` | `just smoke-test-desktop firefox` | Run desktop tests only |
| `just smoke-test-check` | Check prerequisites | Verify system requirements |

### Browser Options
- `chrome` - Chrome/Chromium (default)
- `firefox` - Firefox/Mozilla

### Examples

```bash
# Setup (run once)
just smoke-test-install

# Run all tests with visible Chrome (default behavior)
just smoke-test chrome

# Run only Docker tests with visible Firefox
just smoke-test firefox "Docker"

# Run tests in headless mode (hidden browser)
just smoke-test-headless chrome

# Test specific configuration with visible browser
just smoke-test-config "Docker APScheduler (Development)" firefox

# Check what configurations are available
just smoke-test-list
```

## Test Coverage

The smoke tests automatically detect available configurations and run tests against:

### Web Server Modes (Direct Python)
- **APScheduler mode**: Backend with in-process task scheduling
- **Celery mode**: Backend with Redis and Celery workers (if Redis available)
- Both development and production configurations

### Docker Modes  
- **APScheduler Docker**: Containerized backend with in-process scheduling
- **Celery Docker**: Full containerized stack with Redis and Celery
- Both development and production configurations

### Desktop Modes
- **Desktop app**: Local PyWebView-based application
- **AppImage**: Packaged Linux AppImage
- **Flatpak**: Flatpak package (if available)

## Test Flow

Each configuration test performs:

1. **Start Application**: Launch the specific configuration
2. **Health Check**: Verify backend health endpoint responds
3. **Frontend Interaction**: 
   - Load test image
   - Set coin parameters (diameter, thickness, etc.)
   - Verify preview updates
4. **STL Generation**:
   - Click "Generate STL" button
   - Wait for generation to complete
   - Download generated STL file
5. **STL Validation**: Basic validation of STL file format
6. **Cleanup**: Stop application and clean up files

## Usage

```bash
# Run all available smoke tests
just smoke-test

# Run specific configuration
just smoke-test-web-apscheduler
just smoke-test-docker-dev-celery
just smoke-test-desktop

# Run with specific browser
just smoke-test --browser firefox

# Run with verbose output
just smoke-test --verbose
```

## Requirements

- Python 3.11+
- Selenium WebDriver
- Chrome/Chromium or Firefox browser
- Docker (for Docker tests)
- Flatpak (for Flatpak tests)

## Test Image

The tests use `tests/assets/test-coin-image.png` - a simple high-contrast image suitable for coin generation testing.