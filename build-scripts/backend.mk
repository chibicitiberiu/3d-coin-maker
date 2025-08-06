# Backend Build Management  
# Creates virtual environments with correct dependencies and configuration

# Use a stamp file to track build completion
$(BUILD_BACKEND)/.build_complete: validate-all install-deps $(BUILD_BACKEND)
	$(call log_target_start,Building Backend)
	$(call log_step,Creating Python virtual environment)
	@cd backend && python3 -m venv ../$(BUILD_BACKEND)/venv
	$(call log_step,Upgrading pip and installing Poetry)
	@cd backend && ../$(BUILD_BACKEND)/venv/bin/pip install --upgrade pip poetry
	$(call log_step,Installing dependencies with Poetry (this may take a moment))
	@cd backend && \
		if [ "$(MODE)" = "debug" ]; then \
			echo "[36m    Installing development dependencies[B[m"; \
			VIRTUAL_ENV=../$(BUILD_BACKEND)/venv ../$(BUILD_BACKEND)/venv/bin/poetry install --with=dev; \
		else \
			echo "[36m    Installing production dependencies only[B[m"; \
			VIRTUAL_ENV=../$(BUILD_BACKEND)/venv ../$(BUILD_BACKEND)/venv/bin/poetry install --only=main; \
		fi
	@touch $(BUILD_BACKEND)/.build_complete
	$(call log_target_complete,Backend Build)

build-backend: $(BUILD_BACKEND)/.build_complete

$(BUILD_BACKEND):
	@mkdir -p $(BUILD_BACKEND)


run-backend: build-backend build-deps
	$(call log_target_start,Starting Backend Server)
	@if [ "$(SCHEDULER)" != "apscheduler" ]; then \
		$(call log_error,Local run-backend only supports apscheduler scheduler); \
		$(call log_info,For celery, use Docker deployment instead); \
		exit 1; \
	fi
	@if [ ! -f "$(BUILD_BACKEND)/venv/bin/python" ]; then \
		$(call log_error,Python executable not found. Build may be incomplete.); \
		$(call log_info,Run 'make clean-backend && make build-backend' to rebuild.); \
		exit 1; \
	fi
	$(call log_step,Starting Python backend server)
	$(call log_info,Server will be available on port $(BACKEND_PORT))
	@export HMM_BINARY_PATH="$(BUILD_HMM_BINARY)" && \
	cd $(BACKEND_SRC) && \
	../$(BUILD_BACKEND)/venv/bin/python main.py --run \
		$(if $(filter true,$(DEBUG_FLAG)),--debug) \
		--scheduler $(SCHEDULER) \
		--port $(BACKEND_PORT)

clean-backend:
	$(call log_step,Cleaning backend builds)
	@rm -rf $(BUILD_BACKEND)
	$(call log_step,Removing Python cache files)
	@cd $(BACKEND_SRC) && \
		rm -rf __pycache__ && \
		find . -name "*.pyc" -delete && \
		find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
		rm -rf dist build .pytest_cache .ruff_cache
	$(call log_info,Backend build cleaned) 

venv-backend: build-backend
	$(call log_step,Starting backend shell with activated environment)
	@cd $(BACKEND_SRC) && . ../$(BUILD_BACKEND)/venv/bin/activate && export PS1="(venv-backend) \u@\h:\w\$$ " && ([ -f ~/.bashrc ] && . ~/.bashrc || [ -f ~/.bash_profile ] && . ~/.bash_profile || true) && exec bash -i

.PHONY: build-backend run-backend clean-backend venv-backend