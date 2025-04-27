# cmake file for Raspberry Pi Pico 2 W

set(PICO_BOARD "pico2_w")
set(PICO_FLASH_SIZE_BYTES 16777216)
# To change the gpio count for QFN-80
# set(PICO_NUM_GPIOS 48)

set(MICROPY_PY_LWIP ON)
set(MICROPY_PY_NETWORK_CYW43 ON)

# Bluetooth
set(MICROPY_PY_BLUETOOTH ON)
set(MICROPY_BLUETOOTH_BTSTACK ON)
set(MICROPY_PY_BLUETOOTH_CYW43 ON)

# Board specific version of the frozen manifest
set(MICROPY_FROZEN_MANIFEST ${MICROPY_BOARD_DIR}/manifest.py)

list(APPEND MICROPY_DEF_BOARD
    "MICROPY_HW_ENABLE_PSRAM=1"
    "MICROPY_GC_SPLIT_HEAP=1"
)