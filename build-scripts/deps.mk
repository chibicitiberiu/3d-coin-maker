# Dependencies Management
# Handles third-party dependencies and system requirements

build-deps: $(BUILD_HMM_BINARY)

$(EXTERNAL_SRC)/hmm:
	$(call log_step,Cloning HMM library)
	@mkdir -p $(EXTERNAL_SRC)
	@git clone https://github.com/fogleman/hmm.git $(EXTERNAL_SRC)/hmm

$(BUILD_HMM_BINARY): $(EXTERNAL_SRC)/hmm
	$(call log_target_start,Building HMM Library)
	@mkdir -p $(BUILD_HMM)
	@if [ -f "$(BUILD_HMM_BINARY)" ] && [ -x "$(BUILD_HMM_BINARY)" ]; then \
		$(call log_info,HMM binary already exists and is executable, skipping build); \
	else \
		$(call log_step,Updating HMM repository); \
		cd $(EXTERNAL_SRC)/hmm && git pull; \
		$(call log_step,Compiling HMM (this may take a moment)); \
		cd $(EXTERNAL_SRC)/hmm && \
		make clean || true && \
		make && \
		chmod +x hmm && \
		cp hmm ../../$(BUILD_HMM_BINARY); \
		$(call log_step,Creating symlink for easy access); \
		cd $(BUILD_ROOT) && ln -sf $(BUILD_HMM_BINARY) hmm; \
	fi
	$(call log_target_complete,HMM Library Build)

clean-deps:
	$(call log_step,Cleaning dependencies)
	@rm -rf $(BUILD_EXTERNAL)
	$(call log_info,Dependencies cleaned)

.PHONY: build-deps install-deps clean-deps