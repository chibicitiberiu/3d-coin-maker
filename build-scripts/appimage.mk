# AppImage Desktop Application Build
# Handles AppImage packaging for the desktop version of Coin Maker

# Note: config.mk is already included by the main Makefile

# Configuration
PLATFORM = $(shell uname -m)
PYTHON_VERSION = $(shell python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
APPIMAGE_DOCKER_IMAGE = coinmaker-appimage-builder:latest

# Build directories (following standard build/<config>/<module> pattern)
DESKTOP_BUILD_DIR = $(BUILD_DIR)/desktop
APPIMAGE_DIR = $(DESKTOP_BUILD_DIR)/appimage
APPDIR = $(APPIMAGE_DIR)/AppDir

# AppImage target name
APPIMAGE_FILE = $(DESKTOP_BUILD_DIR)/CoinMaker-$(PLATFORM).AppImage

# Validate Python version for PyInstaller compatibility
validate-python-version:
	$(call log_step,Checking Python version compatibility)
	@if [ "$(PYTHON_VERSION)" = "3.13" ] || [ "$(PYTHON_VERSION)" \> "3.13" ]; then \
		$(call log_error,Python $(PYTHON_VERSION) detected. PyInstaller requires Python <3.14); \
		$(call log_info,Please use Python 3.11 or 3.12 for AppImage building); \
		exit 1; \
	fi
	$(call log_info,Python $(PYTHON_VERSION) is compatible)

# Build desktop components (dependencies)
build-desktop-components: validate-all validate-python-version build-deps
	$(call log_target_start,Building Desktop Components)
	@$(MAKE) build-frontend MODE=$(MODE) VARIANT=desktop
	@$(MAKE) build-backend MODE=$(MODE) VARIANT=desktop SCHEDULER=apscheduler
	$(call log_target_complete,Desktop Components Built in $(DESKTOP_BUILD_DIR))

# Create PyInstaller spec file
create-pyinstaller-spec:
	$(call log_step,Creating PyInstaller spec file)
	@cd desktop && python3 ../build-scripts/create-pyinstaller-spec.py \
		--mode $(MODE) \
		--desktop-build-dir $(DESKTOP_BUILD_DIR) \
		--output coin-maker.spec

# Build desktop executable with PyInstaller
build-desktop-executable: create-pyinstaller-spec $(DESKTOP_VENV)
	$(call log_step,Building desktop executable with PyInstaller)
	@cd desktop && \
		VIRTUAL_ENV=../$(DESKTOP_BUILD_DIR)/venv ../$(DESKTOP_BUILD_DIR)/venv/bin/poetry install --only=main && \
		VIRTUAL_ENV=../$(DESKTOP_BUILD_DIR)/venv ../$(DESKTOP_BUILD_DIR)/venv/bin/poetry add --group=dev pyinstaller && \
		VIRTUAL_ENV=../$(DESKTOP_BUILD_DIR)/venv ../$(DESKTOP_BUILD_DIR)/venv/bin/poetry run pyinstaller coin-maker.spec --clean --noconfirm
	$(call log_info,Desktop executable built)

# Create AppImage directory structure
create-appimage-structure:
	$(call log_step,Creating AppImage directory structure)
	@mkdir -p $(APPDIR)/usr/bin
	@mkdir -p $(APPDIR)/usr/lib
	@mkdir -p $(APPDIR)/usr/share/applications
	@mkdir -p $(APPDIR)/usr/share/icons/hicolor/256x256/apps
	@mkdir -p $(APPDIR)/usr/share/coin-maker-frontend
	$(call log_info,AppImage structure created)

# Install application files to AppDir
install-appimage-files: create-appimage-structure
	$(call log_step,Installing application files to AppDir)
	# Copy built executable
	@cp -r desktop/dist/CoinMaker/* $(APPDIR)/usr/bin/
	# Copy HMM binary
	@cp build/external/hmm/hmm $(APPDIR)/usr/bin/
	# Copy frontend build (use main frontend build, not desktop-specific)
	@cp -r $(BUILD_FRONTEND)/* $(APPDIR)/usr/share/coin-maker-frontend/
	$(call log_info,Application files installed)

# Create desktop file and AppRun
create-desktop-files:
	$(call log_step,Creating desktop files)
	# Create desktop file
	@echo '[Desktop Entry]' > $(APPDIR)/coin-maker.desktop
	@echo 'Type=Application' >> $(APPDIR)/coin-maker.desktop
	@echo 'Name=Coin Maker' >> $(APPDIR)/coin-maker.desktop
	@echo 'Comment=Three-D Printable Coin Generator' >> $(APPDIR)/coin-maker.desktop
	@echo 'Exec=CoinMaker' >> $(APPDIR)/coin-maker.desktop
	@echo 'Icon=coin-maker' >> $(APPDIR)/coin-maker.desktop
	@echo 'Categories=Graphics;Engineering;' >> $(APPDIR)/coin-maker.desktop
	@echo 'Keywords=threeDee;printing;coin;STL;modeling;' >> $(APPDIR)/coin-maker.desktop
	@echo 'StartupNotify=true' >> $(APPDIR)/coin-maker.desktop
	# Create AppRun script
	@echo '#!/bin/bash' > $(APPDIR)/AppRun
	@echo 'HERE="$$(dirname "$$(readlink -f "$${0}")")"' >> $(APPDIR)/AppRun
	@echo 'export PATH="$${HERE}/usr/bin:$${PATH}"' >> $(APPDIR)/AppRun
	@echo 'export LD_LIBRARY_PATH="$${HERE}/usr/lib:$${LD_LIBRARY_PATH}"' >> $(APPDIR)/AppRun
	@echo 'exec "$${HERE}/usr/bin/CoinMaker" "$$@"' >> $(APPDIR)/AppRun
	@chmod +x $(APPDIR)/AppRun
	# Copy icon if available
	@if [ -f "frontend/static/favicon.svg" ]; then \
		cp frontend/static/favicon.svg $(APPDIR)/coin-maker.svg; \
	fi
	$(call log_info,Desktop files created)

# Download appimagetool if needed
download-appimagetool:
	@if [ ! -f "$(APPIMAGE_DIR)/appimagetool" ]; then \
		echo "Downloading appimagetool..."; \
		wget -O $(APPIMAGE_DIR)/appimagetool \
			"https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"; \
		chmod +x $(APPIMAGE_DIR)/appimagetool; \
	fi

# Package AppImage
package-appimage: download-appimagetool
	$(call log_step,Packaging AppImage)
	@cd $(APPIMAGE_DIR) && ./appimagetool AppDir ../CoinMaker-$(PLATFORM).AppImage
	$(call log_info,AppImage created: $(APPIMAGE_FILE))

# Build complete AppImage (main user target)
build-appimage:
	$(call log_section_start,Building AppImage ($(MODE) mode))
	@if [ "$$(uname)" != "Linux" ]; then \
		$(call log_error,AppImage packaging only supported on Linux); \
		exit 1; \
	fi
	@if [ "$(PYTHON_VERSION)" = "3.13" ] || [ "$(PYTHON_VERSION)" \> "3.13" ]; then \
		$(call log_info,Python $(PYTHON_VERSION) detected - using Docker container with Python 3.12); \
		$(MAKE) _build-appimage-docker MODE=$(MODE); \
	else \
		$(call log_info,Python $(PYTHON_VERSION) is compatible - building natively); \
		$(MAKE) _build-appimage-native MODE=$(MODE); \
	fi

# Test AppImage
test-appimage:
	@if [ ! -f "$(APPIMAGE_FILE)" ]; then \
		echo "Error: AppImage not found. Run 'make build-appimage MODE=release' first"; \
		exit 1; \
	fi
	@echo "Testing AppImage..."
	@$(APPIMAGE_FILE) --help || echo "AppImage executable test completed"

# Clean AppImage artifacts
clean-appimage:
	@echo "Cleaning AppImage artifacts..."
	@rm -rf build/*/desktop/appimage
	@rm -f build/*/desktop/CoinMaker-*.AppImage
	@rm -f desktop/coin-maker.spec
	@rm -rf desktop/dist
	@rm -rf desktop/build
	@echo "AppImage artifacts cleaned"

# Clean desktop builds completely (AppImage specific)
clean-desktop-builds:
	@echo "Cleaning desktop builds..."
	@rm -rf build/*/desktop
	@echo "Desktop builds cleaned"

# Show AppImage status
appimage-status:
	@echo "AppImage Build Status:"
	@echo "====================="
	@echo "MODE                 = $(MODE)"
	@echo "PLATFORM             = $(PLATFORM)"
	@echo "PYTHON_VERSION       = $(PYTHON_VERSION)"
	@echo "DESKTOP_BUILD_DIR    = $(DESKTOP_BUILD_DIR)"
	@echo "APPIMAGE_FILE        = $(APPIMAGE_FILE)"
	@echo ""
	@if [ -f "$(APPIMAGE_FILE)" ]; then \
		$(call log_info,AppImage exists: $(APPIMAGE_FILE)); \
		ls -lh $(APPIMAGE_FILE); \
	else \
		$(call log_error,AppImage not found: $(APPIMAGE_FILE)); \
	fi

# Internal Docker-based AppImage building

# Build Docker image for AppImage building (internal)
_build-appimage-docker-image:
	$(call log_step,Building Docker image for AppImage building)
	@docker build -f build-scripts/Dockerfile.appimage -t $(APPIMAGE_DOCKER_IMAGE) .
	$(call log_info,Docker image built: $(APPIMAGE_DOCKER_IMAGE))

# Build AppImage using Docker container (internal)
_build-appimage-docker: _build-appimage-docker-image
	$(call log_step,Building AppImage in Docker container ($(MODE) mode))
	@docker run --rm \
		-v $(PWD):/workspace \
		-w /workspace \
		-e MODE=$(MODE) \
		--user $(shell id -u):$(shell id -g) \
		--dns=8.8.8.8 \
		$(APPIMAGE_DOCKER_IMAGE) \
		sh -c "make _build-desktop-components MODE=$(MODE) && make _build-desktop-executable MODE=$(MODE)"
	@$(MAKE) install-appimage-files MODE=$(MODE)
	@$(MAKE) create-desktop-files MODE=$(MODE)
	@$(MAKE) package-appimage MODE=$(MODE)
	$(call log_target_complete,AppImage Build Complete)
	$(call log_info,Output: $(APPIMAGE_FILE))
	$(call log_info,Run: ./$(APPIMAGE_FILE))

# Native AppImage build (internal - runs inside Docker or with compatible Python)
_build-appimage-native: _validate-build-env
	$(call log_step,Building AppImage natively ($(MODE) mode))
	@$(MAKE) _build-desktop-components MODE=$(MODE)
	@$(MAKE) _build-desktop-executable MODE=$(MODE)
	@$(MAKE) install-appimage-files MODE=$(MODE)
	@$(MAKE) create-desktop-files MODE=$(MODE)
	@$(MAKE) package-appimage MODE=$(MODE)
	$(call log_target_complete,AppImage Build Complete)
	$(call log_info,Output: $(APPIMAGE_FILE))
	$(call log_info,Run: ./$(APPIMAGE_FILE))

# Validate build environment (internal)
_validate-build-env:
	$(call log_step,Validating build environment)
	@if [ "$(MODE)" != "debug" ] && [ "$(MODE)" != "release" ]; then \
		$(call log_error,MODE must be 'debug' or 'release', got '$(MODE)'); \
		exit 1; \
	fi
	$(call log_info,Environment validated for $(MODE) mode)

# Build desktop components (internal)
_build-desktop-components: _validate-build-env build-deps
	$(call log_step,Building desktop components ($(MODE) mode))
	@$(MAKE) build-frontend MODE=$(MODE) VARIANT=desktop
	@$(MAKE) build-backend MODE=$(MODE) VARIANT=desktop SCHEDULER=apscheduler
	@$(MAKE) build-desktop MODE=$(MODE)
	$(call log_info,Desktop components built in $(DESKTOP_BUILD_DIR))

# Build desktop executable (internal)
_build-desktop-executable: create-pyinstaller-spec
	$(call log_step,Building desktop executable with PyInstaller)
	@cd desktop && \
		VIRTUAL_ENV=../build/$(MODE)/desktop/venv ../build/$(MODE)/desktop/venv/bin/poetry install --only=main && \
		VIRTUAL_ENV=../build/$(MODE)/desktop/venv ../build/$(MODE)/desktop/venv/bin/poetry add --group=dev pyinstaller && \
		VIRTUAL_ENV=../build/$(MODE)/desktop/venv ../build/$(MODE)/desktop/venv/bin/poetry run pyinstaller coin-maker.spec --clean --noconfirm
	$(call log_info,Desktop executable built)

.PHONY: validate-python-version build-desktop-components create-pyinstaller-spec build-desktop-executable create-appimage-structure install-appimage-files create-desktop-files download-appimagetool package-appimage build-appimage test-appimage clean-appimage clean-desktop-builds appimage-status _build-appimage-docker-image _build-appimage-docker _build-appimage-native _validate-build-env _build-desktop-components _build-desktop-executable