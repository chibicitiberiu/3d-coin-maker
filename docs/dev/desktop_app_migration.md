# Desktop App Migration Plan

## Overview

Convert the Coin Maker web application into a cross-platform desktop application while maintaining the option for self-hosted web deployment. The strategy uses **Eel** to wrap the existing Django backend and SvelteKit frontend into a native desktop application.

## Goals

- **Primary**: Desktop application for easy distribution and zero hosting costs
- **Secondary**: Maintain web version for self-hosting enthusiasts
- **Constraints**: Minimal code duplication, leverage existing architecture
- **Timeline**: 4-6 weeks development effort

## Architecture Changes

### Current Architecture
```
Frontend (SvelteKit) ←→ Backend (Django + DRF) ←→ Celery + Redis
```

### Target Desktop Architecture
```
Desktop App:
├── Eel Wrapper (native window)
├── Django Backend (simplified)
├── APScheduler (replaces Celery)
├── SvelteKit Frontend (minimal changes)
└── Bundled Python Runtime
```

### Target Web Architecture (Maintained)
```
Web App:
├── Docker Container
├── Django Backend (full featured)
├── Celery + Redis
└── SvelteKit Frontend (same codebase)
```

## Migration Phases

### Phase 1: Task Queue Abstraction (Week 1)
**Goal**: Abstract task queue implementation to support both Celery and APScheduler

#### 1.1 Create Task Queue Interface
```python
# backend/core/interfaces/task_queue.py
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class TaskQueue(ABC):
    @abstractmethod
    def enqueue(self, task_name: str, args: tuple, kwargs: Dict[str, Any]) -> str:
        """Enqueue a task and return task ID"""
        pass
    
    @abstractmethod
    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and result"""
        pass
    
    @abstractmethod
    def start(self) -> None:
        """Start the task queue"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop the task queue"""
        pass
```

#### 1.2 Implement Celery Adapter
```python
# backend/core/services/celery_queue.py
from .task_queue import TaskQueue
from apps.processing import tasks

class CeleryTaskQueue(TaskQueue):
    def enqueue(self, task_name: str, args: tuple, kwargs: Dict[str, Any]) -> str:
        task_func = getattr(tasks, task_name)
        result = task_func.delay(*args, **kwargs)
        return result.id
    
    # ... implement other methods
```

#### 1.3 Implement APScheduler Adapter
```python
# backend/core/services/apscheduler_queue.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import uuid
from .task_queue import TaskQueue

class APSchedulerTaskQueue(TaskQueue):
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.results = {}  # In-memory result store
    
    def enqueue(self, task_name: str, args: tuple, kwargs: Dict[str, Any]) -> str:
        task_id = str(uuid.uuid4())
        # ... implement task execution with result storage
    
    # ... implement other methods
```

#### 1.4 Update Dependency Injection
```python
# backend/core/containers/application.py
from dependency_injector import containers, providers
from core.services.celery_queue import CeleryTaskQueue
from core.services.apscheduler_queue import APSchedulerTaskQueue
import os

class Container(containers.DeclarativeContainer):
    # ... existing services
    
    task_queue = providers.Factory(
        CeleryTaskQueue if os.getenv('USE_CELERY', 'true').lower() == 'true' 
        else APSchedulerTaskQueue
    )
```

### Phase 2: Eel Integration (Week 2)

#### 2.1 Install Dependencies
```bash
cd backend/
poetry add eel apscheduler
```

#### 2.2 Create Desktop Entry Point
```python
# backend/desktop_main.py
import eel
import os
import sys
import threading
import time
from pathlib import Path
from django.core.management import execute_from_command_line
from django.core.wsgi import get_wsgi_application

def start_django_server():
    """Start Django development server in background thread"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coin_maker.settings')
    os.environ.setdefault('USE_CELERY', 'false')
    
    # Start Django server
    execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])

def main():
    # Set up paths
    backend_dir = Path(__file__).parent
    frontend_build_dir = backend_dir.parent / 'frontend' / 'build'
    
    # Start Django in background thread
    django_thread = threading.Thread(target=start_django_server, daemon=True)
    django_thread.start()
    
    # Wait for Django to start
    time.sleep(3)
    
    # Initialize Eel with built frontend
    eel.init(str(frontend_build_dir))
    
    # Start Eel app
    eel.start('index.html', 
              size=(1400, 900),
              port=0,  # Use random port for Eel
              host='localhost',
              block=True)

if __name__ == '__main__':
    main()
```

#### 2.3 Add Native File Dialogs
```python
# backend/desktop_main.py (additions)
import tkinter as tk
from tkinter import filedialog

@eel.expose
def open_file_dialog():
    """Open native file dialog for image selection"""
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    file_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"),
            ("All files", "*.*")
        ]
    )
    return file_path

@eel.expose
def save_file_dialog(default_filename="coin.stl"):
    """Open native save dialog for STL export"""
    root = tk.Tk()
    root.withdraw()
    
    file_path = filedialog.asksaveasfilename(
        title="Save STL File",
        defaultextension=".stl",
        filetypes=[("STL files", "*.stl"), ("All files", "*.*")],
        initialvalue=default_filename
    )
    return file_path
```

### Phase 3: Frontend Adaptations (Week 2-3)

#### 3.1 Platform Detection
```typescript
// frontend/src/lib/platform.ts
export const isDesktopApp = () => {
    return window.eel !== undefined;
};

export const isWebApp = () => {
    return !isDesktopApp();
};
```

#### 3.2 File Handling Abstraction
```typescript
// frontend/src/lib/fileHandler.ts
import { isDesktopApp } from './platform';

declare global {
    interface Window {
        eel: any;
    }
}

export class FileHandler {
    static async selectImage(): Promise<File | null> {
        if (isDesktopApp()) {
            const filePath = await window.eel.open_file_dialog()();
            if (filePath) {
                // Convert file path to File object for desktop
                const response = await fetch(`file://${filePath}`);
                const blob = await response.blob();
                return new File([blob], filePath.split('/').pop() || 'image');
            }
            return null;
        } else {
            // Web file input handling
            return new Promise((resolve) => {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'image/*';
                input.onchange = (e) => {
                    const file = (e.target as HTMLInputElement).files?.[0];
                    resolve(file || null);
                };
                input.click();
            });
        }
    }

    static async saveSTL(blob: Blob, filename: string): Promise<void> {
        if (isDesktopApp()) {
            const filePath = await window.eel.save_file_dialog()(filename);
            if (filePath) {
                // Save file via backend API
                const formData = new FormData();
                formData.append('file', blob);
                formData.append('path', filePath);
                await fetch('/api/save-file/', {
                    method: 'POST',
                    body: formData
                });
            }
        } else {
            // Web download
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        }
    }
}
```

#### 3.3 Update Main Component
```svelte
<!-- frontend/src/routes/+page.svelte (minimal changes) -->
<script lang="ts">
    import { FileHandler } from '$lib/fileHandler';
    import { isDesktopApp } from '$lib/platform';
    
    // Replace file input handling
    async function handleImageSelect() {
        const file = await FileHandler.selectImage();
        if (file) {
            // Process file as before
            processImageFile(file);
        }
    }
    
    // Replace STL download
    async function handleSTLDownload(blob: Blob) {
        await FileHandler.saveSTL(blob, `coin_${Date.now()}.stl`);
    }
    
    // Rest of component remains the same
</script>

<!-- Conditional UI based on platform -->
{#if isDesktopApp()}
    <button on:click={handleImageSelect}>Select Image</button>
{:else}
    <input type="file" accept="image/*" on:change={handleFileInput} />
{/if}
```

### Phase 4: Build System Updates (Week 3)

#### 4.1 Frontend Build Configuration
```json
// frontend/package.json (add script)
{
  "scripts": {
    "build:desktop": "vite build --mode desktop",
    "build:web": "vite build --mode web"
  }
}
```

```typescript
// frontend/vite.config.ts (add desktop mode)
export default defineConfig(({ mode }) => ({
  // ... existing config
  define: {
    __DESKTOP_APP__: mode === 'desktop'
  }
}));
```

#### 4.2 Desktop Settings Module
```python
# backend/coin_maker/settings_desktop.py
from .settings import *

# Desktop-specific settings
USE_CELERY = False
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Disable CORS for desktop
CORS_ALLOW_ALL_ORIGINS = True

# Simplified logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

### Phase 5: Packaging (Week 4-5)

#### 5.1 PyInstaller Configuration
```python
# backend/desktop.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['desktop_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
        ('../frontend/build', 'frontend/build'),
        ('core/templates', 'core/templates'),
    ],
    hiddenimports=[
        'django.core.management.commands.runserver',
        'apps.api.views',
        'apps.processing.tasks',
        'core.services',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CoinMaker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'
)
```

#### 5.2 Build Scripts
```bash
#!/bin/bash
# scripts/build-desktop.sh

set -e

echo "Building desktop application..."

# Build frontend
cd frontend/
pnpm install
pnpm run build:desktop
cd ..

# Build backend
cd backend/
poetry install

# Install PyInstaller if not present
poetry add --group=dev pyinstaller

# Build executable
poetry run pyinstaller desktop.spec --clean --noconfirm

echo "Desktop app built in backend/dist/"
```

```powershell
# scripts/build-desktop.ps1 (Windows)
Write-Host "Building desktop application for Windows..."

# Build frontend
Set-Location frontend
pnpm install
pnpm run build:desktop
Set-Location ..

# Build backend
Set-Location backend
poetry install
poetry add --group=dev pyinstaller

# Build executable
poetry run pyinstaller desktop.spec --clean --noconfirm

Write-Host "Desktop app built in backend/dist/"
```

#### 5.3 GitHub Actions for Releases
```yaml
# .github/workflows/desktop-release.yml
name: Desktop App Release

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Poetry
        uses: snok/install-poetry@v1
        
      - name: Build Frontend
        run: |
          cd frontend
          npm install -g pnpm
          pnpm install
          pnpm run build:desktop
          
      - name: Build Desktop App
        run: |
          cd backend
          poetry install
          poetry add --group=dev pyinstaller
          poetry run pyinstaller desktop.spec --clean --noconfirm
          
      - name: Upload Windows Build
        uses: actions/upload-artifact@v4
        with:
          name: coin-maker-windows
          path: backend/dist/CoinMaker.exe

  build-macos:
    runs-on: macos-latest
    # Similar steps for macOS
    
  build-linux:
    runs-on: ubuntu-latest
    # Similar steps for Linux
    
  release:
    needs: [build-windows, build-macos, build-linux]
    runs-on: ubuntu-latest
    steps:
      - name: Download All Artifacts
        uses: actions/download-artifact@v4
        
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          files: |
            coin-maker-windows/CoinMaker.exe
            coin-maker-macos/CoinMaker.app
            coin-maker-linux/CoinMaker
```

### Phase 6: Testing & Polish (Week 5-6)

#### 6.1 Desktop-Specific Testing
- [ ] File dialog integration
- [ ] Window sizing and positioning
- [ ] Application icon and metadata
- [ ] Startup time optimization
- [ ] Error handling for missing dependencies
- [ ] Auto-updater integration (optional)

#### 6.2 Cross-Platform Testing
- [ ] Windows 10/11 (PyInstaller executable)
- [ ] macOS Intel and Apple Silicon
- [ ] Linux (AppImage or native package)

#### 6.3 Documentation Updates
- [ ] Desktop installation instructions
- [ ] Building from source guide
- [ ] Troubleshooting common issues
- [ ] Feature comparison (desktop vs web)

## Dual Distribution Strategy

### Desktop Releases (Primary)
- GitHub Releases with pre-built executables
- Automatic updates via GitHub API
- Single-file distribution (PyInstaller onefile)
- Platform-specific installers (optional)

### Web Version (Secondary)
- Docker Hub images for self-hosting
- Docker Compose files for easy setup
- Documentation for advanced users
- Same codebase, different build target

## Risk Mitigation

### Technical Risks
- **PyInstaller compatibility**: Use version 5.13.0, test thoroughly
- **Native dependencies**: HMM library needs manual compilation
- **Startup time**: Optimize Django initialization for desktop
- **File permissions**: Handle file system access properly

### Distribution Risks
- **Code signing**: Required for macOS/Windows trust
- **Anti-virus detection**: PyInstaller executables sometimes flagged
- **Size limitations**: Bundle optimization needed

### Maintenance Risks
- **Dual codebase complexity**: Minimize with shared modules
- **Platform-specific bugs**: Establish testing pipeline
- **Dependency updates**: Coordinate between web/desktop versions

## Success Metrics

### Technical Metrics
- [ ] Startup time < 10 seconds
- [ ] Package size < 200MB per platform
- [ ] STL generation performance matches web version
- [ ] Zero hosting costs achieved

### User Experience Metrics
- [ ] One-click installation experience
- [ ] Native file handling working
- [ ] Feature parity with web version
- [ ] Offline functionality confirmed

## Timeline Summary

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Task Queue Abstraction | APScheduler integration, shared interfaces |
| 2 | Eel Integration | Desktop entry point, native dialogs |
| 2-3 | Frontend Adaptations | Platform detection, file handling |
| 3 | Build System | Desktop build configs, settings |
| 4-5 | Packaging | PyInstaller setup, CI/CD pipeline |
| 5-6 | Testing & Polish | Cross-platform testing, documentation |

## Next Steps

1. **Validate approach**: Create minimal Eel prototype with existing app
2. **Plan development**: Set up feature branch for desktop migration
3. **Begin Phase 1**: Start with task queue abstraction
4. **Establish testing**: Set up cross-platform build environment

This migration plan maintains the existing web functionality while creating a robust desktop application suitable for open-source distribution.