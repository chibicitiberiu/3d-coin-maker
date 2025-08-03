# Application Packaging
# Handles PyInstaller specs and AppImage creation

# Import required modules
import "dependencies.just"
import "frontend.just"

# Configuration
platform := arch()
appimage_dir := "build/appimage"

# Create PyInstaller spec file
create-pyinstaller-spec mode="prod":
    cd backend && python3 -c 'import sys; open("coin-maker.spec", "w").write("""# -*- mode: python ; coding: utf-8 -*-\n\nimport os\nfrom pathlib import Path\n\n# Get current directory\ncurrent_dir = Path(__file__).parent\n\nblock_cipher = None\n\n# Define data files to include\ndatas = [\n    # Frontend build\n    (str(current_dir / "../build/frontend"), "frontend/build"),\n    # HMM binary\n    (str(current_dir / "../build/external/hmm/hmm"), "."),\n    # Configuration files\n    (str(current_dir / "../config"), "config"),\n]\n\n# Hidden imports for all the modules PyInstaller might miss\nhiddenimports = [\n    "fastapi",\n    "uvicorn",\n    "uvicorn.lifespan",\n    "uvicorn.lifespan.on",\n    "uvicorn.loops",\n    "uvicorn.loops.auto",\n    "uvicorn.protocols",\n    "uvicorn.protocols.http",\n    "uvicorn.protocols.http.auto",\n    "uvicorn.protocols.websockets",\n    "uvicorn.protocols.websockets.auto",\n    "pydantic",\n    "pydantic_settings",\n    "pywebview",\n    "apscheduler",\n    "manifold3d",\n    "trimesh",\n    "PIL",\n    "numpy",\n    "core.services",\n    "core.interfaces",\n    "api.routes",\n    "apps",\n]\n\na = Analysis(\n    ["desktop_main.py"],\n    pathex=[],\n    binaries=[],\n    datas=datas,\n    hiddenimports=hiddenimports,\n    hookspath=[],\n    hooksconfig={},\n    runtime_hooks=[],\n    excludes=[\n        "celery",  # Exclude web-only dependencies in desktop mode\n        "redis",\n    ],\n    win_no_prefer_redirects=False,\n    win_private_assemblies=False,\n    cipher=block_cipher,\n    noarchive=False,\n)\n\npyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)\n\nexe = EXE(\n    pyz,\n    a.scripts,\n    [],\n    exclude_binaries=True,\n    name="CoinMaker",\n    debug=False,\n    bootloader_ignore_signals=False,\n    strip=False,\n    upx=True,\n    console=False,  # Hide console window\n    disable_windowed_traceback=False,\n    argv_emulation=False,\n    target_arch=None,\n    codesign_identity=None,\n    entitlements_file=None,\n)\n\ncoll = COLLECT(\n    exe,\n    a.binaries,\n    a.zipfiles,\n    a.datas,\n    strip=False,\n    upx=True,\n    upx_exclude=[],\n    name="CoinMaker",\n)\n""")'
    echo "PyInstaller spec created: backend/coin-maker.spec"

# Create desktop file for AppImage
create-desktop-file:
    #!/usr/bin/env bash
    set -e
    echo "Creating desktop file..."
    
    # Create desktop file
    echo "[Desktop Entry]" > {{appimage_dir}}/AppDir/coin-maker.desktop
    echo "Type=Application" >> {{appimage_dir}}/AppDir/coin-maker.desktop
    echo "Name=Coin Maker" >> {{appimage_dir}}/AppDir/coin-maker.desktop
    echo "Comment=Three-D Printable Coin Generator" >> {{appimage_dir}}/AppDir/coin-maker.desktop
    echo "Exec=CoinMaker" >> {{appimage_dir}}/AppDir/coin-maker.desktop
    echo "Icon=coin-maker" >> {{appimage_dir}}/AppDir/coin-maker.desktop
    echo "Categories=Graphics;ThreeDGraphics;Engineering;" >> {{appimage_dir}}/AppDir/coin-maker.desktop
    echo "Keywords=threeDee;printing;coin;STL;modeling;" >> {{appimage_dir}}/AppDir/coin-maker.desktop
    echo "StartupNotify=true" >> {{appimage_dir}}/AppDir/coin-maker.desktop
    
    # Create AppRun script
    echo '#!/bin/bash' > {{appimage_dir}}/AppDir/AppRun
    echo 'HERE="$(dirname "$(readlink -f "${0}")")"' >> {{appimage_dir}}/AppDir/AppRun
    echo 'export PATH="${HERE}/usr/bin:${PATH}"' >> {{appimage_dir}}/AppDir/AppRun
    echo 'export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"' >> {{appimage_dir}}/AppDir/AppRun
    echo 'exec "${HERE}/usr/bin/CoinMaker" "$@"' >> {{appimage_dir}}/AppDir/AppRun
    
    chmod +x {{appimage_dir}}/AppDir/AppRun
    
    # Copy icon (create simple one if not exists)
    if [ ! -f "{{appimage_dir}}/AppDir/usr/share/icons/hicolor/256x256/apps/coin-maker.png" ]; then
        # Create a simple icon using ImageMagick or copy from frontend
        if [ -f "frontend/static/favicon.svg" ]; then
            cp frontend/static/favicon.svg {{appimage_dir}}/AppDir/coin-maker.svg
        fi
    fi
    
    echo "Desktop file created"

# Download AppImage tools and create final AppImage
package-appimage:
    #!/usr/bin/env bash
    set -e
    echo "Packaging AppImage..."
    
    # Download appimagetool if not exists
    if [ ! -f "{{appimage_dir}}/appimagetool" ]; then
        echo "Downloading appimagetool..."
        wget -O {{appimage_dir}}/appimagetool \
            "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        chmod +x {{appimage_dir}}/appimagetool
    fi
    
    # Create AppImage
    cd {{appimage_dir}}
    ./appimagetool AppDir ../CoinMaker-{{platform}}.AppImage
    cd ../..
    
    echo "AppImage packaged: build/CoinMaker-{{platform}}.AppImage"

# Create AppImage package for Linux
build-appimage mode="prod":
    #!/usr/bin/env bash
    set -e
    echo "Creating AppImage ({{mode}} mode)..."
    
    # Only support Linux for AppImage
    if [ "$(uname)" != "Linux" ]; then
        echo "Error: AppImage packaging only supported on Linux"
        exit 1
    fi
    
    # Build desktop app first - use desktop mode for frontend
    just build-hmm
    just install-deps
    just build-frontend desktop
    
    # Create AppImage directory structure
    mkdir -p {{appimage_dir}}/AppDir/usr/bin
    mkdir -p {{appimage_dir}}/AppDir/usr/lib
    mkdir -p {{appimage_dir}}/AppDir/usr/share/applications
    mkdir -p {{appimage_dir}}/AppDir/usr/share/icons/hicolor/256x256/apps
    
    # Install backend
    echo "Installing backend to AppDir..."
    cd backend
    poetry install --only=main
    
    # Create PyInstaller spec if not exists
    if [ ! -f "coin-maker.spec" ]; then
        just create-pyinstaller-spec {{mode}}
    fi
    
    # Check Python version for PyInstaller compatibility
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ "$python_version" == "3.13" ]] || [[ "$python_version" > "3.13" ]]; then
        echo "Warning: Python $python_version detected. PyInstaller requires Python <3.14"
        echo "Please use Python 3.11 or 3.12 for AppImage building"
        echo "You can install a compatible Python version and create a virtual environment"
        exit 1
    fi
    
    # Build with PyInstaller
    poetry add --group=dev pyinstaller
    poetry run pyinstaller coin-maker.spec --clean --noconfirm
    
    # Copy built application
    cp -r dist/CoinMaker/* ../{{appimage_dir}}/AppDir/usr/bin/
    cd ..
    
    # Copy HMM binary
    cp build/external/hmm/hmm {{appimage_dir}}/AppDir/usr/bin/
    
    # Copy frontend build
    cp -r build/frontend {{appimage_dir}}/AppDir/usr/share/coin-maker-frontend
    
    # Create desktop file
    just create-desktop-file
    
    # Create AppImage
    just package-appimage
    
    echo "AppImage created: build/CoinMaker-{{platform}}.AppImage"

# Build Flatpak package
build-flatpak mode="prod":
    #!/usr/bin/env bash
    set -e
    echo "Building Flatpak package ({{mode}} mode)..."
    
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
    just build-hmm
    
    # Create build directory
    mkdir -p build/flatpak
    
    # Build the Flatpak
    flatpak-builder \
        --force-clean \
        --repo=build/flatpak/repo \
        build/flatpak/build-dir \
        io.github.coinmaker.CoinMaker.yaml
    
    echo "Flatpak built successfully!"
    echo "To install locally: flatpak install --user build/flatpak/repo io.github.coinmaker.CoinMaker"

# Install Flatpak locally for testing
install-flatpak:
    #!/usr/bin/env bash
    set -e
    echo "Installing Flatpak locally..."
    
    if [ ! -d "build/flatpak/repo" ]; then
        echo "Error: Flatpak not built yet. Run 'just build-flatpak' first."
        exit 1
    fi
    
    # Install from local repo
    flatpak install --user -y build/flatpak/repo io.github.coinmaker.CoinMaker
    
    echo "Flatpak installed! Run with: flatpak run io.github.coinmaker.CoinMaker"

# Uninstall Flatpak
uninstall-flatpak:
    #!/usr/bin/env bash
    set -e
    echo "Uninstalling Flatpak..."
    flatpak uninstall --user -y io.github.coinmaker.CoinMaker || echo "Flatpak not installed"
    echo "Flatpak uninstalled"

# Export Flatpak bundle for distribution
export-flatpak:
    #!/usr/bin/env bash
    set -e
    echo "Exporting Flatpak bundle..."
    
    if [ ! -d "build/flatpak/repo" ]; then
        echo "Error: Flatpak not built yet. Run 'just build-flatpak' first."
        exit 1
    fi
    
    # Create bundle
    flatpak build-bundle \
        build/flatpak/repo \
        build/CoinMaker-{{platform}}.flatpak \
        io.github.coinmaker.CoinMaker
    
    echo "Flatpak bundle created: build/CoinMaker-{{platform}}.flatpak"