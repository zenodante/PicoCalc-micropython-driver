

# MicroPython Drivers for PicoCalc
![REPL](./imgs/framebuffer.jpg)
## Build Instructions

```
Folder structure:

|
|- micropython                      # Clone the MicroPython repo here
|   |- ports
|      |- rp2
|         |- build                 # Create this build folder
|         |- modules               # Place all py files from pico_files/modules/
|
|- PicoCalc-micropython-driver     # Driver modules
|   |- picocalcdisplay
|   |- vtterminal
|
|- Any additional modules (e.g., ulab, etc.)
```

Build MicroPython as usual, while including user modules:
```sh
cd micropython/ports/rp2
git submodule update --init --recursive
mkdir build && cd build
cmake .. \
  -DUSER_C_MODULES="Path/To/PicoCalc-micropython-driver/picocalcdisplay/micropython.cmake;Path/To/PicoCalc-micropython-driver/vtterminal/micropython.cmake" \
  -DMICROPY_BOARD=[TARGET_BOARD]
```

Supported `TARGET_BOARD` values:
- `RPI_PICO`
- `RPI_PICO2`
- `RPI_PICO2_W`

(Other boards are untested.)

---

## Installation

- Flash the compiled `.uf2` to your Pico as usual.
- **Place only `main.py` in the root directory.**
- **Delete all existing `.py` files in `/lib`** (e.g., `fbconsole.py`, `picocalc.py`, etc.).  
  > These modules are already *frozen* into the firmware!

Using Thonny is the easiest method for file transfer and interaction.

---

## Features

### ✅ Keyboard Driver  
Fully functional and tested. Works seamlessly with vt100 terminal emulator.

### ✅ ILI9488 Display Driver (C module + Python interface)  
- C module supports high-speed 1/2/4/8-bit LUT drawing and 16-bit 565RGB.  
- Python wrapper uses `framebuf` interface and handles display swapping.  
- Display updates now run on `core1` for a smoother REPL experience.

### ✅ screen capture
- Using ctrl + u to capture screen buffer into your sd card. currently only at the root of the sd card
The Data is in raw type. For default 16 color framebuff copy, it is 50kB each. Left pixel in high 4 bit.
Standard vt 100 16 color map may use to rebuild the image. I will upload a python script to convert it.

### 🔲 Speaker Driver  
Not available yet.


---

## Usage Notes

You can launch the built-in Python code editor by calling:
```python
edit("abc.py")
```
![editor](./imgs/framebuffer2.jpg)
Editor is based on [robert-hh/Micropython-Editor](https://github.com/robert-hh/Micropython-Editor)  
Now with keyword highlighting support.

The REPL and editor both run inside a VT100 terminal emulator, based on  
[ht-deko/vt100_stm32](https://github.com/ht-deko/vt100_stm32), with bug fixes and additional features.

---

## Credits
- [robert-hh/Micropython-Editor](https://github.com/robert-hh/Micropython-Editor)  
- [ht-deko/vt100_stm32](https://github.com/ht-deko/vt100_stm32)
- `sdcard.py` is from the official MicroPython repository:  
  [micropython-lib/sdcard.py](https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py)
