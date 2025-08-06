#!/usr/bin/env python3
"""
Create PyInstaller spec file for Coin Maker desktop application.

This script generates a .spec file for PyInstaller based on the current
build configuration and project structure.
"""

import argparse
import os
import sys
from pathlib import Path


def create_spec_content(mode: str, desktop_build_dir: str) -> str:
    """Generate the PyInstaller spec file content."""
    
    # Calculate the actual values based on mode
    debug_value = "True" if mode == 'debug' else "False"
    console_value = "True" if mode == 'debug' else "False"
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get current directory - use SPECPATH which is always available in PyInstaller
if 'SPECPATH' in globals():
    current_dir = Path(SPECPATH)
else:
    current_dir = Path(os.path.dirname(os.path.abspath(__spec__.origin if '__spec__' in globals() else '.')))

block_cipher = None

# Define data files to include
datas = [
    # Frontend build (same for web and desktop)
    (str(current_dir / "../build/{mode}/frontend"), "frontend/build"),
    # HMM binary
    (str(current_dir / "../build/external/hmm/hmm"), "."),
    # Configuration files
    (str(current_dir / "../config"), "config"),
]

# Hidden imports for all the modules PyInstaller might miss
hiddenimports = [
    "requests",  # Must be first - critical dependency
    "urllib3",
    "certifi",
    "charset_normalizer",
    "idna",
    "requests.adapters",
    "requests.auth",
    "requests.cookies",
    "requests.exceptions", 
    "requests.models",
    "requests.sessions",
    "requests.structures",
    "requests.utils",
    "fastapi",
    "uvicorn",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on", 
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "pydantic",
    "pydantic_settings",
    "pywebview",
    "apscheduler",
    "trimesh",
    "PIL",
    "numpy",
    "core.services",
    "core.interfaces", 
    "api.routes",
    "apps",
    "services",
    "services.sveltekit_server",
    "desktop_app",
    "desktop_webview_manager",
]

a = Analysis(
    ["desktop_main.py"],
    pathex=[str(current_dir), str(current_dir / "../backend"), "/workspace/desktop", "/workspace/backend"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        "celery",  # Exclude web-only dependencies in desktop mode
        "redis",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CoinMaker",
    debug={debug_value},
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={console_value},  # Show console in debug mode
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CoinMaker",
)
'''
    
    return spec_content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create PyInstaller spec file for Coin Maker desktop application"
    )
    parser.add_argument(
        "--mode",
        choices=["debug", "release"],
        default="release",
        help="Build mode (default: release)"
    )
    parser.add_argument(
        "--desktop-build-dir",
        required=True,
        help="Desktop build directory path"
    )
    parser.add_argument(
        "--output",
        default="coin-maker.spec",
        help="Output spec file name (default: coin-maker.spec)"
    )
    
    args = parser.parse_args()
    
    # Generate spec content
    spec_content = create_spec_content(args.mode, args.desktop_build_dir)
    
    # Write to file
    output_path = Path(args.output)
    try:
        with open(output_path, 'w') as f:
            f.write(spec_content)
        print(f"PyInstaller spec created: {output_path}")
    except Exception as e:
        print(f"Error creating spec file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()