# cmake file for Raspberry Pi Pico2
set(PICO_BOARD "pico2")
set(PICO_FLASH_SIZE_BYTES 16777216)

# To change the gpio count for QFN-80
# set(PICO_NUM_GPIOS 48)
list(APPEND MICROPY_DEF_BOARD
    "MICROPY_HW_ENABLE_PSRAM=1"
    "MICROPY_GC_SPLIT_HEAP=1"
)