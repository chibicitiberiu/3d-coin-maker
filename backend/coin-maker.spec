# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Get current directory
current_dir = Path(__file__).parent

block_cipher = None

# Define data files to include
datas = [
    # Frontend build
    (str(current_dir / "../build/frontend"), "frontend/build"),
    # HMM binary
    (str(current_dir / "../build/external/hmm/hmm"), "."),
    # Configuration files
    (str(current_dir / "../config"), "config"),
]

# Hidden imports for all the modules PyInstaller might miss
hiddenimports = [
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
    "manifold3d",
    "trimesh",
    "PIL",
    "numpy",
    "core.services",
    "core.interfaces",
    "api.routes",
    "apps",
]

a = Analysis(
    ["desktop_main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
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
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window
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
