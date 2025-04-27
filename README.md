

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

Copy all files from pico_files/modules/ to micropython/ports/rp2/modules/ folder
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
### With filesystem
The uf2 file already included file system and main.py, boot.py. Just flash it and remove the usb link to the pico module, tune on the picocalc. 
- **NO FILE COPY NEEDED!! The old file system will be destroyed!**

- picocalc_micropython_ulab_eigenmath_withfilesystem_pico2.uf2 (you could use it with your pico 2 or pico 2w module)
Included ulab, eigenmath port (https://github.com/zenodante/eigenmath_micropython), make picocalc a full function advanced calculator!
- picocalc_micropython_withfilesystem_pico.uf2 (for pico)
Only REPL, code editor 
- picocalc_micropython_withfilesystem_pico2.uf2 (for pico 2)
Only REPL, code editor 
- picocalc_micropython_withfilesystem_pico2w.uf2 (for pico 2w)
Only REPL, code editor 

### Without filesystem uf2
the filesystem in the pico module is safe, it won't be overwrite during your firmware upgrade.
- picocalc_micropython_NOfilesystem_pico.uf2
- picocalc_micropython_NOfilesystem_pico2.uf2
- picocalc_micropython_NOfilesystem_pico2w.uf2
- Flash the compiled `.uf2` to your Pico as usual.
- **Place only `main.py,root.py` from pico_files/root/ in the pico root directory.**
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

#### Working with WIFI on picoW/2W
The wifi chip connect to the rp2040/2350 via spi1, which shared with LCD. As we autorefresh the lcd on core1, it is necessary to stop the auto refresh function first via the function:
pc_terminal.stopRefresh(), after wifi finish its work, use pc_terminal.recoverRefresh() to recover the LCD refreshing.

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
