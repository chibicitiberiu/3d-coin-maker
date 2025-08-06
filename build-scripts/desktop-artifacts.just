# Desktop Application Artifacts
# Handles desktop binary, AppImage, and Flatpak builds with proper dependency management

# Import dependencies
import "deps.just"
import "frontend.just"
import "backend.just"

# Configuration
platform := arch()

# Build desktop binary (depends on all component builds)
# Usage: MODE=debug just build-desktop
build-desktop:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters with defaults
    mode="${MODE:-debug}"
    
    # Validate parameters
    if [[ "$mode" != "debug" && "$mode" != "release" ]]; then
        echo "Error: MODE must be 'debug' or 'release', got '$mode'"
        exit 1
    fi
    
    echo "Building desktop application ($mode mode)..."
    
    # Build all dependencies first
    just build-deps
    MODE="$mode" VARIANT="desktop" just build-frontend
    MODE="$mode" VARIANT="desktop" SCHEDULER="apscheduler" just build-backend
    
    # Build directory for this configuration is created by component builds
    
    # Build directory for this configuration
    build_dir="build/desktop_${mode}_apscheduler"
    
    echo "Desktop components built in $build_dir"
    echo "Desktop binary available via run-desktop-local or build-desktop-appimage"

# Build AppImage package (requires release mode)
# Usage: MODE=release just build-desktop-appimage
build-desktop-appimage:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters with defaults
    mode="${MODE:-release}"
    
    # Validate mode
    if [ "$mode" != "release" ]; then
        echo "Error: AppImage requires release mode, got '$mode'"
        exit 1
    fi
    
    # Only support Linux for AppImage
    if [ "$(uname)" != "Linux" ]; then
        echo "Error: AppImage packaging only supported on Linux"
        exit 1
    fi
    
    echo "Creating AppImage ($mode mode)..."
    
    # Ensure desktop build is complete
    MODE="$mode" just build-desktop
    
    # Create AppImage directory structure
    appimage_dir="build/desktop_${mode}_apscheduler/appimage"
    mkdir -p $appimage_dir/AppDir/usr/bin
    mkdir -p $appimage_dir/AppDir/usr/lib
    mkdir -p $appimage_dir/AppDir/usr/share/applications
    mkdir -p $appimage_dir/AppDir/usr/share/icons/hicolor/256x256/apps
    mkdir -p $appimage_dir/AppDir/usr/share/coin-maker-frontend
    
    # Install backend with PyInstaller
    echo "Building backend executable with PyInstaller..."
    cd backend
    poetry install --only=main
    
    # Create PyInstaller spec if not exists
    if [ ! -f "coin-maker.spec" ]; then
        just _create-pyinstaller-spec
    fi
    
    # Check Python version for PyInstaller compatibility
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ "$python_version" == "3.13" ]] || [[ "$python_version" > "3.13" ]]; then
        echo "Warning: Python $python_version detected. PyInstaller requires Python <3.14"
        echo "Please use Python 3.11 or 3.12 for AppImage building"
        exit 1
    fi
    
    # Build with PyInstaller
    poetry add --group=dev pyinstaller
    poetry run pyinstaller coin-maker.spec --clean --noconfirm
    
    # Copy built application
    cp -r dist/CoinMaker/* ../$appimage_dir/AppDir/usr/bin/
    cd ..
    
    # Copy HMM binary
    cp build/external/hmm/hmm $appimage_dir/AppDir/usr/bin/
    
    # Copy frontend build
    cp -r build/desktop_${mode}_apscheduler/frontend/* $appimage_dir/AppDir/usr/share/coin-maker-frontend/
    
    # Create desktop file and AppRun
    just _create-desktop-file
    
    # Create AppImage
    just _package-appimage
    
    echo "AppImage created: build/desktop_${mode}_apscheduler/CoinMaker-$(arch).AppImage"

# Build Flatpak package
# Usage: MODE=release just build-desktop-flatpak
build-desktop-flatpak:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters with defaults
    mode="${MODE:-release}"
    
    # Validate mode
    if [ "$mode" != "release" ]; then
        echo "Error: Flatpak requires release mode, got '$mode'"
        exit 1
    fi
    
    echo "Building Flatpak package ($mode mode)..."
    
    # Check if flatpak-builder is available
    if ! command -v flatpak-builder &> /dev/null; then
        echo "Error: flatpak-builder not found. Install it with:"
        echo "  - Fedora/RHEL: sudo dnf install flatpak-builder"
        echo "  - Ubuntu/Debian: sudo apt install flatpak-builder"
        echo "  - Arch: sudo pacman -S flatpak-builder"
        exit 1
    fi
    
    # Check if Flatpak runtime is installed
    if ! flatpak list --runtime | grep -q "org.freedesktop.Platform.*23.08"; then
        echo "Installing required Flatpak runtime..."
        flatpak install -y flathub org.freedesktop.Platform//23.08
        flatpak install -y flathub org.freedesktop.Sdk//23.08
    fi
    
    # Build dependencies first
    MODE="$mode" just build-desktop
    
    # Create build directory
    mkdir -p build/desktop_${mode}_apscheduler/flatpak
    
    # Build the Flatpak
    flatpak-builder \
        --force-clean \
        --repo=build/desktop_${mode}_apscheduler/flatpak/repo \
        build/desktop_${mode}_apscheduler/flatpak/build-dir \
        io.github.coinmaker.CoinMaker.yaml
    
    echo "Flatpak built successfully!"
    echo "Install locally: just install-desktop-flatpak"

# Install Flatpak locally for testing
install-desktop-flatpak:
    #!/usr/bin/env bash
    set -e
    echo "Installing Flatpak locally..."
    
    if [ ! -d "build/desktop_release_apscheduler/flatpak/repo" ]; then
        echo "Error: Flatpak not built yet. Run 'MODE=release just build-desktop-flatpak' first."
        exit 1
    fi
    
    # Install from local repo
    flatpak install --user -y build/desktop_release_apscheduler/flatpak/repo io.github.coinmaker.CoinMaker
    
    echo "Flatpak installed! Run with: just run-desktop-flatpak"

# Clean desktop builds
# Usage: MODE=debug just clean-desktop (or just clean-desktop for all)
clean-desktop:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters (empty means clean all)
    mode="${MODE:-}"
    
    if [ "$mode" = "" ]; then
        echo "Cleaning all desktop builds..."
        rm -rf build/desktop_*_apscheduler
        echo "All desktop builds cleaned"
    else
        echo "Cleaning desktop build ($mode mode)..."
        rm -rf build/desktop_${mode}_apscheduler
        echo "Desktop build cleaned"
    fi

# Clean AppImage artifacts
clean-desktop-appimage:
    #!/usr/bin/env bash
    set -e
    echo "Cleaning AppImage artifacts..."
    rm -rf build/desktop_*_apscheduler/appimage
    rm -f build/desktop_*_apscheduler/CoinMaker-*.AppImage
    echo "AppImage artifacts cleaned"

# Clean Flatpak artifacts
clean-desktop-flatpak:
    #!/usr/bin/env bash
    set -e
    echo "Cleaning Flatpak artifacts..."
    rm -rf build/desktop_*_apscheduler/flatpak
    rm -f build/desktop_*_apscheduler/CoinMaker-*.flatpak
    echo "Flatpak artifacts cleaned"

# Helper: Create PyInstaller spec file
_create-pyinstaller-spec:
    cd backend && python3 -c 'import sys; open("coin-maker.spec", "w").write("""# -*- mode: python ; coding: utf-8 -*-\n\nimport os\nfrom pathlib import Path\n\n# Get current directory\ncurrent_dir = Path(__file__).parent\n\nblock_cipher = None\n\n# Define data files to include\ndatas = [\n    # Frontend build\n    (str(current_dir / "../build/desktop_release_apscheduler/frontend"), "frontend/build"),\n    # HMM binary\n    (str(current_dir / "../build/external/hmm/hmm"), "."),\n    # Configuration files\n    (str(current_dir / "../config"), "config"),\n]\n\n# Hidden imports for all the modules PyInstaller might miss\nhiddenimports = [\n    "fastapi",\n    "uvicorn",\n    "uvicorn.lifespan",\n    "uvicorn.lifespan.on",\n    "uvicorn.loops",\n    "uvicorn.loops.auto",\n    "uvicorn.protocols",\n    "uvicorn.protocols.http",\n    "uvicorn.protocols.http.auto",\n    "uvicorn.protocols.websockets",\n    "uvicorn.protocols.websockets.auto",\n    "pydantic",\n    "pydantic_settings",\n    "pywebview",\n    "apscheduler",\n    "manifold3d",\n    "trimesh",\n    "PIL",\n    "numpy",\n    "core.services",\n    "core.interfaces",\n    "api.routes",\n    "apps",\n]\n\na = Analysis(\n    ["desktop_main.py"],\n    pathex=[],\n    binaries=[],\n    datas=datas,\n    hiddenimports=hiddenimports,\n    hookspath=[],\n    hooksconfig={},\n    runtime_hooks=[],\n    excludes=[\n        "celery",  # Exclude web-only dependencies in desktop mode\n        "redis",\n    ],\n    win_no_prefer_redirects=False,\n    win_private_assemblies=False,\n    cipher=block_cipher,\n    noarchive=False,\n)\n\npyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)\n\nexe = EXE(\n    pyz,\n    a.scripts,\n    [],\n    exclude_binaries=True,\n    name="CoinMaker",\n    debug=False,\n    bootloader_ignore_signals=False,\n    strip=False,\n    upx=True,\n    console=False,  # Hide console window\n    disable_windowed_traceback=False,\n    argv_emulation=False,\n    target_arch=None,\n    codesign_identity=None,\n    entitlements_file=None,\n)\n\ncoll = COLLECT(\n    exe,\n    a.binaries,\n    a.zipfiles,\n    a.datas,\n    strip=False,\n    upx=True,\n    upx_exclude=[],\n    name="CoinMaker",\n)\n""")'

# Helper: Create desktop file for AppImage
_create-desktop-file:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters with defaults
    mode="${MODE:-release}"
    appimage_dir="build/desktop_${mode}_apscheduler/appimage"
    
    # Create desktop file
    {
        echo "[Desktop Entry]"
        echo "Type=Application"
        echo "Name=Coin Maker"
        echo "Comment=Three-D Printable Coin Generator"
        echo "Exec=CoinMaker"
        echo "Icon=coin-maker"
        echo "Categories=Graphics;ThreeDGraphics;Engineering;"
        echo "Keywords=threeDee;printing;coin;STL;modeling;"
        echo "StartupNotify=true"
    } > $appimage_dir/AppDir/coin-maker.desktop
    
    # Create AppRun script
    {
        echo "#!/bin/bash"
        echo 'HERE="$(dirname "$(readlink -f "${0}")")"'
        echo 'export PATH="${HERE}/usr/bin:${PATH}"'
        echo 'export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"'
        echo 'exec "${HERE}/usr/bin/CoinMaker" "$@"'
    } > $appimage_dir/AppDir/AppRun
    
    chmod +x $appimage_dir/AppDir/AppRun
    
    # Copy icon (create simple one if not exists)
    if [ -f "frontend/static/favicon.svg" ]; then
        cp frontend/static/favicon.svg $appimage_dir/AppDir/coin-maker.svg
    fi

# Helper: Package AppImage
_package-appimage:
    #!/usr/bin/env bash
    set -e
    
    # Get parameters with defaults
    mode="${MODE:-release}"
    appimage_dir="build/desktop_${mode}_apscheduler/appimage"
    
    # Download appimagetool if not exists
    if [ ! -f "$appimage_dir/appimagetool" ]; then
        echo "Downloading appimagetool..."
        wget -O $appimage_dir/appimagetool \
            "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        chmod +x $appimage_dir/appimagetool
    fi
    
    # Create AppImage
    cd $appimage_dir
    ./appimagetool AppDir ../CoinMaker-$(arch).AppImage
    cd ../../..