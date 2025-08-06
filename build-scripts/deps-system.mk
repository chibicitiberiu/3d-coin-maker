# System Dependencies Management
# Handles installation of system-level dependencies across different distributions

# Base package lists for different distributions
UBUNTU_PACKAGES_BASE = python3 python3-pip python3-venv python3-poetry nodejs npm git make gcc g++ cmake libglm-dev
FEDORA_PACKAGES_BASE = python3 python3-pip python3-poetry nodejs npm git make gcc gcc-c++ cmake glm-devel
ARCH_PACKAGES_BASE = python python-pip python-poetry nodejs npm git make gcc cmake glm

# Flatpak packages (optional)
UBUNTU_FLATPAK_PACKAGES = flatpak flatpak-builder
FEDORA_FLATPAK_PACKAGES = flatpak flatpak-builder
ARCH_FLATPAK_PACKAGES = flatpak flatpak-builder

# Final package lists (conditional)
ifeq ($(ENABLE_FLATPAK),true)
UBUNTU_PACKAGES = $(UBUNTU_PACKAGES_BASE) $(UBUNTU_FLATPAK_PACKAGES)
FEDORA_PACKAGES = $(FEDORA_PACKAGES_BASE) $(FEDORA_FLATPAK_PACKAGES)
ARCH_PACKAGES = $(ARCH_PACKAGES_BASE) $(ARCH_FLATPAK_PACKAGES)
else
UBUNTU_PACKAGES = $(UBUNTU_PACKAGES_BASE)
FEDORA_PACKAGES = $(FEDORA_PACKAGES_BASE)
ARCH_PACKAGES = $(ARCH_PACKAGES_BASE)
endif

# pnpm installation via npm
PNPM_INSTALL_CMD = npm install -g pnpm

# Check if command exists
check-command = $(shell command -v $(1) 2>/dev/null)

install-system-deps:
	$(call log_target_start,Installing System Dependencies)
	@if [ -f /etc/os-release ]; then \
		. /etc/os-release; \
		case "$$ID" in \
			ubuntu|debian) \
				$(call log_step,Installing packages for Ubuntu/Debian); \
				sudo apt-get update; \
				sudo apt-get install -y $(UBUNTU_PACKAGES); \
				;; \
			fedora) \
				$(call log_step,Installing packages for Fedora); \
				sudo dnf install -y $(FEDORA_PACKAGES); \
				;; \
			arch|manjaro) \
				$(call log_step,Installing packages for Arch Linux); \
				sudo pacman -S --noconfirm $(ARCH_PACKAGES); \
				;; \
			*) \
				$(call log_error,Unsupported distribution: $$ID); \
				$(call log_info,Please install manually:); \
				$(call log_info,- Python 3 with pip and venv); \
				$(call log_info,- Node.js with npm); \
				$(call log_info,- Git, make, gcc/g++, cmake); \
				$(call log_info,- GLM development headers (libglm-dev/glm-devel/glm)); \
				exit 1; \
				;; \
		esac; \
	else \
		$(call log_error,Cannot detect distribution - /etc/os-release not found); \
		exit 1; \
	fi
	@$(MAKE) install-pnpm
	$(call log_target_complete,System Dependencies Installation)

install-pnpm:
	@if ! $(call check-command,pnpm); then \
		$(call log_step,Installing pnpm); \
		$(PNPM_INSTALL_CMD); \
	else \
		$(call log_info,pnpm already installed: $$(pnpm --version)); \
	fi

check-system-deps:
	$(call log_target_start,Checking System Dependencies)
	$(call log_info,ENABLE_FLATPAK=$(ENABLE_FLATPAK))
	@commands="python3 poetry pnpm git make gcc cmake"; \
	if [ "$(ENABLE_FLATPAK)" = "true" ]; then \
		commands="$$commands flatpak flatpak-builder"; \
	fi; \
	for cmd in $$commands; do \
		if $(call check-command,$$cmd) >/dev/null; then \
			echo "✓ $$cmd: $$($$cmd --version 2>/dev/null | head -1 || echo 'installed')"; \
		else \
			echo "✗ $$cmd: not found"; \
		fi; \
	done
	@echo "Checking GLM headers..."
	@if [ -f "/usr/include/glm/glm.hpp" ] || [ -f "/usr/local/include/glm/glm.hpp" ]; then \
		echo "✓ GLM headers: found"; \
	else \
		echo "✗ GLM headers: not found"; \
	fi
	@echo "Platform: $$(uname -s) $$(uname -m)"

.PHONY: install-system-deps install-pnpm check-system-deps