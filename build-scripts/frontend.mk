# Frontend Build Management
# Handles frontend builds with mode (debug/release) configurations
# Scheduler is runtime-only and doesn't affect frontend builds

# Configuration tracking
FRONTEND_CONFIG_FILE = $(FRONTEND_SRC)/.last_config
CURRENT_CONFIG = $(MODE)

# Auto-clean if configuration changed
ifneq ($(shell cat $(FRONTEND_CONFIG_FILE) 2>/dev/null),$(CURRENT_CONFIG))
build-frontend: _clean-frontend-src-and-rebuild
else
# Main frontend target  
build-frontend: _build-frontend-direct
endif

_build-frontend-direct: validate-all install-deps $(FRONTEND_SRC)/node_modules
	$(call log_target_start,Building Frontend)
	$(call log_step,Creating build directory)
	@mkdir -p $(BUILD_FRONTEND)
	$(call log_step,Running pnpm build (this may take a moment))
	$(call log_info,Output will be saved to $(BUILD_FRONTEND))
	@cd $(FRONTEND_SRC) && \
		MODE=$(NPM_MODE) \
		BUILD_OUTPUT="../$(BUILD_FRONTEND)" \
		pnpm run build
	@echo "$(CURRENT_CONFIG)" > $(FRONTEND_CONFIG_FILE) || echo "Warning: Could not save frontend config (read-only filesystem)"
	$(call log_target_complete,Frontend Build)

_clean-frontend-src-and-rebuild: _clean-frontend-src
	@$(MAKE) _build-frontend-direct

$(FRONTEND_SRC)/node_modules: $(FRONTEND_SRC)/package.json $(FRONTEND_SRC)/pnpm-lock.yaml
	$(call log_step,Installing frontend dependencies)
	$(call log_info,Running pnpm install (this may take a moment))
	@cd $(FRONTEND_SRC) && pnpm install $(PNPM_INSTALL_ARGS)
	@touch $(FRONTEND_SRC)/node_modules

run-frontend-dev: $(FRONTEND_SRC)/node_modules
	@export BUILD_DIR="$(BUILD_DIR)" && \
	export FRONTEND_SRC="$(FRONTEND_SRC)" && \
	export NPM_MODE="$(NPM_MODE)" && \
	./scripts/run-wrapper.sh --mode $(MODE) --scheduler $(SCHEDULER) --backend-port $(BACKEND_PORT) --frontend-type dev --only-frontend

_clean-frontend-src:
	$(call log_warning,Configuration changed - cleaning frontend source directory)
	$(call log_step,Removing node_modules and build artifacts)
	@cd $(FRONTEND_SRC) && \
		rm -rf node_modules && \
		rm -rf .svelte-kit && \
		rm -rf dist && \
		rm -rf build && \
		find . -name "*.log" -delete && \
		find . -name ".vite" -type d -exec rm -rf {} + 2>/dev/null || true
	@rm -rf $(FRONTEND_CONFIG_FILE)
	$(call log_info,Frontend source directory cleaned)

run-frontend: build-frontend
	@export BUILD_DIR="$(BUILD_DIR)" && \
	export FRONTEND_SRC="$(FRONTEND_SRC)" && \
	export NPM_MODE="$(NPM_MODE)" && \
	./scripts/run-wrapper.sh --mode $(MODE) --scheduler $(SCHEDULER) --backend-port $(BACKEND_PORT) --frontend-type preview --only-frontend

clean-frontend: _clean-frontend-src
	$(call log_step,Cleaning frontend builds)
	@rm -rf $(BUILD_FRONTEND)
	@rm -rf build/.pnpm-store build/.pnpm-cache
	$(call log_info,Frontend builds cleaned)

.PHONY: build-frontend run-frontend-dev run-frontend clean-frontend _build-frontend-direct _clean-frontend-src-and-rebuild _clean-frontend-src