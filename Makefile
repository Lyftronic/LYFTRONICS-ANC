# Decky Plugin Database CI/CD Makefile
OUT_DIR = backend/out
SRC_DIR = backend/src

all: $(OUT_DIR)/librnnoise_ladspa.so

$(OUT_DIR)/librnnoise_ladspa.so:
	@echo "Creating directories..."
	mkdir -p $(OUT_DIR)
	mkdir -p $(SRC_DIR)
	@echo "Fetching open-source repository..."
	if [ ! -d "$(SRC_DIR)/noise-suppression-for-voice" ]; then \
		git clone https://github.com/werman/noise-suppression-for-voice.git $(SRC_DIR)/noise-suppression-for-voice; \
	fi
	@echo "Executing CMake build process..."
	cd $(SRC_DIR)/noise-suppression-for-voice && cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_LADSPA_PLUGIN=ON -DBUILD_LV2_PLUGIN=OFF -DBUILD_VST_PLUGIN=OFF -DBUILD_VST3_PLUGIN=OFF
	cd $(SRC_DIR)/noise-suppression-for-voice && cmake --build build --config Release
	@echo "Routing compiled binary to Decky CI output directory..."
	cp $(SRC_DIR)/noise-suppression-for-voice/build/bin/ladspa/librnnoise_ladspa.so $(OUT_DIR)/
	@echo "Build sequence complete."

clean:
	rm -rf $(OUT_DIR) $(SRC_DIR)/noise-suppression-for-voice
