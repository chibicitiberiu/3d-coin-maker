# Desktop Application Management
# Handles desktop app building and running using the desktop/ module

# Desktop module setup variables
DESKTOP_SRC := desktop
BUILD_DESKTOP := $(BUILD_DIR)/desktop
DESKTOP_VENV := $(BUILD_DESKTOP)/venv

# Desktop builds depend on frontend and backend builds plus desktop module setup
build-desktop: build-frontend build-backend $(DESKTOP_VENV)
	$(call log_target_complete,Desktop Module Ready)

# Desktop Python environment setup
$(DESKTOP_VENV): $(DESKTOP_SRC)/pyproject.toml
	$(call log_target_start,Setting Up Desktop Environment)
	$(call log_step,Creating Python virtual environment)
	@mkdir -p $(BUILD_DESKTOP)
	cd $(DESKTOP_SRC) && python -m venv ../$(BUILD_DESKTOP)/venv
	$(call log_step,Installing Poetry)
	cd $(DESKTOP_SRC) && ../$(BUILD_DESKTOP)/venv/bin/pip install --upgrade pip
	cd $(DESKTOP_SRC) && ../$(BUILD_DESKTOP)/venv/bin/pip install poetry
	$(call log_step,Installing desktop dependencies)
	cd $(DESKTOP_SRC) && VIRTUAL_ENV=../$(BUILD_DESKTOP)/venv ../$(BUILD_DESKTOP)/venv/bin/poetry install

run-desktop: build-desktop build-deps
	$(call log_target_start,Starting Desktop Application)
	@if [ "$(SCHEDULER)" != "apscheduler" ]; then \
		$(call log_warning,Desktop only supports apscheduler scheduler); \
		$(call log_info,Desktop mode will automatically use apscheduler); \
	fi
	@if [ ! -f "$(DESKTOP_VENV)/bin/python" ]; then \
		$(call log_error,Desktop environment not found. Build may be incomplete.); \
		$(call log_info,Run 'make clean-desktop && make build-desktop' to rebuild.); \
		exit 1; \
	fi
	@if [ ! -d "$(BUILD_FRONTEND)" ] || [ ! -f "$(BUILD_FRONTEND)/index.html" ]; then \
		$(call log_error,Frontend build not found at $(BUILD_FRONTEND)); \
		$(call log_info,Run 'make build-frontend' to build the frontend first); \
		exit 1; \
	fi
	$(call log_step,Launching desktop application)
	@export HMM_BINARY_PATH="$(abspath $(BUILD_HMM_BINARY))" && \
	export FRONTEND_BUILD_DIR="$(abspath $(BUILD_FRONTEND))" && \
	cd $(DESKTOP_SRC) && ../$(BUILD_DESKTOP)/venv/bin/python desktop_main.py

clean-desktop:
	$(call log_step,Cleaning desktop builds)
	@rm -rf $(BUILD_DESKTOP)

venv-desktop: build-desktop
	$(call log_step,Starting desktop shell with activated environment)
	@cd $(DESKTOP_SRC) && . ../$(BUILD_DESKTOP)/venv/bin/activate && export PS1="(venv-desktop) \u@\h:\w\$$ " && ([ -f ~/.bashrc ] && . ~/.bashrc || [ -f ~/.bash_profile ] && . ~/.bash_profile || true) && exec bash -i

.PHONY: build-desktop run-desktop clean-desktop venv-desktop