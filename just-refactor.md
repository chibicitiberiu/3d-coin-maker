# Build System Refactor Plan

## Overview
Reorganize the just build scripts from the current mixed structure to a clean artifacts-first approach with consistent naming and better separation of concerns.

## Core Design Principles
- **Artifacts-first approach**: Docker images, AppImages, Flatpaks are all build artifacts
- **Environment variable parameters**: `MODE=debug VARIANT=web SCHEDULER=celery` (uppercase, any order)
- **Clear separation**: Components → Artifacts → Runtime
- **Future-proof naming**: `build-deps` instead of `build-hmm`
- **Build isolation**: Each config builds in `build/<variant>_<mode>_<scheduler>/`

## Build Directory Convention
```
build/
├── web_debug_apscheduler/
├── web_release_celery/
├── desktop_debug_apscheduler/
├── desktop_release_apscheduler/
└── artifacts/
    ├── CoinMaker-x86_64.AppImage
    ├── CoinMaker-x86_64.flatpak
    └── docker/  # tagged images
```

## Docker Image Naming Convention
```
coinmaker:web_debug_apscheduler
coinmaker:web_release_celery
coinmaker:desktop_debug_apscheduler  # (if we ever containerize desktop)
```

## New File Structure
```
build-scripts/
├── deps.just              # Third-party dependencies (HMM, system deps)
├── frontend.just          # Frontend component builds
├── backend.just           # Backend component builds  
├── docker.just            # Docker image artifacts
├── desktop-artifacts.just # Desktop binary artifacts
├── flatpak-artifacts.just # Flatpak artifacts
├── run.just              # Runtime commands
├── utilities.just        # Clean, format, lint, typecheck
└── smoke-test.just       # Testing (enhanced)
```

## New Command Structure

### Component Commands (Low-level, reusable)
```bash
# deps.just
just build-deps                    # HMM + future deps
just install-deps                  # poetry/pnpm deps
just clean-deps

# frontend.just  
MODE=debug VARIANT=web just build-frontend
MODE=release VARIANT=desktop just build-frontend
just clean-frontend                # cleans all, or:
MODE=debug VARIANT=web just clean-frontend

# backend.just
MODE=debug VARIANT=web SCHEDULER=celery just build-backend
MODE=release VARIANT=desktop just build-backend  # always apscheduler
MODE=debug VARIANT=web just clean-backend
```

### Artifact Commands (Build outputs)
```just
# docker.just (web only)
build-web-docker mode="debug|release" scheduler="apscheduler|celery"
publish-web-docker mode="debug|release" scheduler="apscheduler|celery" registry="..."
clean-web-docker [mode] [scheduler]

# desktop-artifacts.just
build-desktop mode="debug|release"           # -> build/desktop_<mode>_apscheduler/coinmaker
build-desktop-appimage mode="release"        # -> build/artifacts/CoinMaker-x86_64.AppImage
build-desktop-flatpak mode="release"         # -> build/artifacts/CoinMaker-x86_64.flatpak
install-desktop-flatpak
clean-desktop [mode]
clean-desktop-appimage
clean-desktop-flatpak

# flatpak-artifacts.just
build-desktop-flatpak mode="release"         # -> build/artifacts/CoinMaker-x86_64.flatpak
install-desktop-flatpak                      # Install locally for testing
clean-desktop-flatpak
```

### Runtime Commands (Using artifacts)
```just
# run.just
run-desktop-local mode="debug|release"       # Development script
run-desktop mode="release"                   # Binary directly
run-desktop-appimage                         # .AppImage file
run-desktop-flatpak                          # Flatpak package

run-web-local mode="debug|release" scheduler="apscheduler|celery" # Local web server
run-web-docker mode="debug|release" scheduler="apscheduler|celery" # Docker compose up

stop-web-docker [mode] [scheduler]
logs-web-docker [mode] [scheduler] [service]
```

### Testing Commands
```just
# smoke-test.just (enhanced)
smoke-test mode="debug|release" variant="web|desktop" scheduler="apscheduler|celery" browser="chrome"
smoke-test-install
smoke-test-check
```

### Utility Commands
```just
# utilities.just
clean                        # Clean everything
clean target                 # Clean specific target (frontend, backend, docker, desktop, etc.)
format
lint
typecheck
```

## Commands Migration

### ✅ KEPT (with modifications)
- `format`, `lint`, `typecheck` - utilities.just
- `smoke-test-install`, `smoke-test-check` - smoke-test.just
- `install-deps` - deps.just

### 🔄 TRANSFORMED
| Old Command | New Command(s) |
|-------------|----------------|
| `build-hmm` | `build-deps` |
| `build-frontend [mode]` | `build-frontend mode="debug/release" variant="web/desktop"` |
| `build-desktop [mode]` | `build-desktop mode="debug/release"` |
| `run-docker [mode] [profile]` | `run-web-docker mode="debug/release" scheduler="apscheduler/celery"` |
| `build-appimage [mode]` | `build-desktop-appimage mode="release"` |
| `build-flatpak [mode]` | `build-desktop-flatpak mode="release"` |
| `run-desktop [mode]` | `run-desktop-local mode="debug/release"` |
| `clean` | `clean` + `clean <target>` |

### ❌ DELETED (redundant/confusing)
- `dev-setup`, `dev-build`, `prod-build` - replaced by specific build commands
- `dev`, `prod`, `flatpak` - replaced by specific workflows
- `docker-dev`, `docker-prod` - replaced by `run-web-docker`
- `docker-logs`, `restart-docker`, `stop-docker` - replaced by `logs-web-docker`, etc.
- `run-docker-detached` - replaced by `run-web-docker` (always detached)
- `clean-docker` - replaced by `clean-web-docker`
- `docker-status`, `test-docker-config` - not essential
- `dev-frontend`, `preview-frontend` - can use `run-web-local`
- `version`, `info`, `help` - `just` without args shows command list
- `audit`, `test` - can be added back if needed
- All the verbose smoke-test variants - replaced by single parameterized command

### ➕ NEW COMMANDS
- All the `clean-<target>` commands for selective cleaning
- `publish-web-docker` for registry publishing
- `install-desktop-flatpak` for local Flatpak testing
- `stop-web-docker`, `logs-web-docker` for Docker management
- Enhanced `smoke-test` with full configuration options

## Implementation Strategy

1. **Create new module files** alongside existing ones
2. **Implement component commands first** (deps, frontend, backend)
3. **Add artifact commands** (docker, desktop, flatpak)
4. **Add runtime commands** (run.just)
5. **Update main justfile** to import new modules
6. **Test new commands** work correctly
7. **Remove old modules** once migration is complete

## Current Implementation Status **REALITY CHECK**

### ✅ **COMPLETED (~25%)**
- **File Structure**: All 8 module files created and deployed to `build-scripts/`
- **Dependencies Module**: `deps.just` - ✅ fully functional (no env vars needed)
- **Frontend Module**: `frontend.just` - ✅ **100% complete with environment variables**
  - ✅ `MODE=debug VARIANT=web just build-frontend` implemented
  - ✅ Build isolation: `build/web_debug_apscheduler/frontend/`
  - ✅ Parameter validation and flexible ordering
- **Backend Module**: `backend.just` - ✅ **100% complete with environment variables**
  - ✅ `MODE=debug VARIANT=web SCHEDULER=celery just build-backend` implemented
  - ✅ Build isolation: `build/web_debug_celery/backend/`
  - ✅ Full parameter validation (MODE, VARIANT, SCHEDULER)
- **Main Justfile**: ✅ **DEPLOYED** as primary justfile with 66 commands

### ❌ **NOT IMPLEMENTED - Still Using Old Template Syntax**
- **Docker Module**: `docker.just` - ❌ Uses `build-web-docker mode="debug" scheduler="apscheduler"`
  - Should be: `MODE=debug SCHEDULER=apscheduler just build-web-docker`
- **Desktop Artifacts**: `desktop-artifacts.just` - ❌ Uses `build-desktop mode="debug"`
  - Should be: `MODE=debug just build-desktop`
- **Runtime Module**: `run.just` - ❌ Uses `run-desktop-local mode="debug"`
  - Should be: `MODE=debug just run-desktop-local`
- **Utilities Module**: `utilities.just` - ❌ Uses `clean-target target`
  - Should be: `TARGET=frontend just clean-target`
- **Smoke Test Module**: `smoke-test.just` - ❌ Uses complex template parameters
  - Should be: `MODE=debug VARIANT=web SCHEDULER=apscheduler BROWSER=chrome just smoke-test`

### 🔄 **MAJOR WORK REMAINING (~75%)**
1. **Convert 5 modules** to environment variable syntax
2. **Update all command documentation** and help text
3. **Fix main justfile workflows** to use proper env var syntax
4. **Test end-to-end functionality** 
5. **Resolve template escaping issues** in docker.just

### 🎯 **Next Steps**
1. **Priority 1**: Convert desktop-artifacts.just to environment variables
2. **Priority 2**: Convert docker.just to environment variables
3. **Priority 3**: Convert run.just, utilities.just, smoke-test.just
4. **Priority 4**: Update main justfile workflow commands
5. **Priority 5**: End-to-end testing and validation

## Benefits **PARTIALLY ACHIEVED**

✅ **File structure** - clean modular organization in `build-scripts/`
✅ **Reduced command count** - 66 commands vs 100+ before
🔄 **Naming patterns** - partially consistent (some modules still use old syntax)
✅ **Build isolation** - `build/<variant>_<mode>_<scheduler>/` structure implemented
✅ **Clear separation** - components vs artifacts vs runtime organization
🔄 **Environment variables** - only 3/8 modules fully converted
❌ **Consistent syntax** - mixed old template + new environment variable syntax
✅ **Modular structure** - clean imports and organization
❌ **Complete migration** - old system replaced but new system not fully implemented

## **REALITY: ~25% Complete**
The refactor **started well** but is **incomplete**. Only frontend and backend modules fully use the new environment variable approach. The majority of commands still use the old template parameter syntax, making the system inconsistent and not meeting the design goals.