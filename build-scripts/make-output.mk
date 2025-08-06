# Make Output Prettification
# Provides standardized logging and visual formatting for make targets

# Color definitions (use tput for portability)
COLOR_RESET := $(shell tput sgr0 2>/dev/null)
COLOR_BOLD := $(shell tput bold 2>/dev/null)
COLOR_GREEN := $(shell tput setaf 2 2>/dev/null)
COLOR_BLUE := $(shell tput setaf 4 2>/dev/null)
COLOR_YELLOW := $(shell tput setaf 3 2>/dev/null)
COLOR_CYAN := $(shell tput setaf 6 2>/dev/null)
COLOR_RED := $(shell tput setaf 1 2>/dev/null)

# Section delimiter
SECTION_LINE := ================================================================================

# Logging functions
define log_section_start
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)$(SECTION_LINE)$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)$(1)$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)$(SECTION_LINE)$(COLOR_RESET)"
endef

define log_target_start
	@echo ""
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)→ $(1)$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)  Configuration: MODE=$(MODE) SCHEDULER=$(SCHEDULER)$(COLOR_RESET)"
	@echo ""
endef

define log_target_complete
	@echo ""
	@echo "$(COLOR_BOLD)$(COLOR_GREEN)✓ $(1) completed$(COLOR_RESET)"
	@echo ""
endef

define log_step
	@echo "$(COLOR_YELLOW)  • $(1)$(COLOR_RESET)"
endef

define log_info
	@echo "$(COLOR_CYAN)    $(1)$(COLOR_RESET)"
endef

define log_warning
	@echo "$(COLOR_BOLD)$(COLOR_YELLOW)⚠ $(1)$(COLOR_RESET)"
endef

define log_error
	@echo "$(COLOR_BOLD)$(COLOR_RED)✗ $(1)$(COLOR_RESET)"
endef

# Configuration display (enhanced)
define show_build_config
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)Build Configuration:$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)  MODE:          $(COLOR_BOLD)$(MODE)$(COLOR_RESET) $(COLOR_CYAN)(build-time)$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)  SCHEDULER:     $(COLOR_BOLD)$(SCHEDULER)$(COLOR_RESET) $(COLOR_CYAN)(runtime-only)$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)  BACKEND_PORT:  $(COLOR_BOLD)$(BACKEND_PORT)$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)  BUILD_DIR:     $(COLOR_BOLD)$(BUILD_DIR)$(COLOR_RESET)"
	@echo ""
endef

.PHONY: show-config
show-config:
	$(call log_section_start,Current Build Configuration)
	$(call show_build_config)