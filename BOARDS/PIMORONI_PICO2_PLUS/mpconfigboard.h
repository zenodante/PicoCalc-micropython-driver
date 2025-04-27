// Board and hardware specific configuration
#define MICROPY_HW_BOARD_NAME                   "\nPimoroni Pico Plus 2 (PSRAM)"
#define MICROPY_HW_FLASH_STORAGE_BYTES          (PICO_FLASH_SIZE_BYTES - (2 * 1024 * 1024))

#define MICROPY_HW_PSRAM_CS_PIN                 47