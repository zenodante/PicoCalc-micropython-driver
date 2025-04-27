# MicroPython Drivers for PicoCalc 
<p align="center">
  <img src="./imgs/framebuffer.jpg" alt="REPL" width="320"/>
</p>

## :bangbang: Updates

- Eigenmath is now included, bringing some actual calculator functionality back to the PicoCalc.
It is available for import in both versions, however if a lite version is wanted (would save about 250kb) I could compile them.

    Thank [@zerodante](https://github.com/zenodante) for his work on it!

<p align="center">
  <img src="./imgs/eigenmath.jpg" alt="Eigenmath Example" width="320"/>
</p>

- Install instructions simplified!
Install instructions now allow just an upload of the full /libs folder, and have been simplified to avoid confusion.

## :building_construction: Build Instructions

```
Folder structure:

|
|- micropython                     # Clone the MicroPython repo here
|   |- ports
|      |- rp2
|         |- modules               # Place all py files from pico_files/modules/ if you want them added internally
|
|- PicoCalc-micropython            # Driver modules
|   |- picocalcdisplay
|   |- vtterminal
|   |- eigenmath_micropython
|
|- Any additional modules (e.g., ulab, etc.)
```

First initalize the repository with:
```sh
cd PicoCalc-micropython
git submodule update --init --recursive
```

Then Build MicroPython as usual, while including user modules:
```sh
cd ../micropython/ports/rp2
git submodule update --init --recursive
mkdir build && cd build
cmake .. \
-DUSER_C_MODULES="location/of/PicoCalc-micropython/picocalcdisplay/micropython.cmake; \
location/of/PicoCalc-micropython/vtterminal/micropython.cmake; \
location/of/micropython-cppmem/micropython.cmake; \
location/of/PicoCalc-micropython/eigenmath_micropython/micropython.cmake" \
-DMICROPY_BOARD=TARGET_BOARD
```

Supported `TARGET_BOARD` values:
- `RPI_PICO`
- `RPI_PICO2`
- `RPI_PICO2_W`
  
IF USING HOMEBREW DEFINITIONS:
- `PIMORONI_PICO2_PLUS`
- `PIMORONI_PICO2_PLUS_W`
  
To use "homebrew" board definitions, copy them to you `/micropython/ports/rp2/boards` folder
(Other boards are untested.)

:warning: **NOTE:** The homebrew board definitions are NOT the official Pimoroni board definitions, they are the basic Pico2 definitions tailored to work with the Pimoroni board via enabling PSRAM and the WiFi stack as nessecary. They are tested and work with the PicoCalc, but **may** lack some functionality like PIO.

---

## Installation

- Flash the compiled `.uf2` to your Pico as usual.
- **Place only `main.py,root.py` from pico_files/root/ in the pico root directory.**
- **Upload whole `/libs` folder to the root directory as it contains nessecary libraries.**
**Note: I may also create uf2 with libs folder frozen in automatically, with no need to copy, however I do not really like this as it removes the ability to easily tweak them on device. Request it if you want it**


Using Thonny is the easiest method for file transfer and interaction.

If the flash nuke is needed, flash as normal, however **DO NOT UNPLUG** until the on-board light flashes to indicate it is done.
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

#### :warning: Working with WiFi on PicoW/2W
Due to the WiFi chip connecting to the RP2040/2350 via SPI1, which is shared with LCD, it is necessary to stop the auto refresh function first via the function:
pc_terminal.stopRefresh(), after wifi finish its work, use pc_terminal.recoverRefresh() to recover the LCD refreshing.

You can launch the built-in Python code editor by calling:
```python
edit("abc.py")
```
Using eigenmath
```python
import eigenmath
em = eigenmath.EigenMath(300*1024) #the internal heap size, eigenmath need A LOT OF RAM. It will be released after you delete the em
em.statue() #show current resource statue
em.run("d(sin(x),x)") #do math calculation, check the eigenmath manual for more details
em.reset() #reset the internal sources

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
- `sdcard.py` is from the official MicroPython repository: [micropython-lib/sdcard.py](https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py)
- `flash_nuke.uf2` is from the Raspberry Pi Documentation: [Resetting Flash Memory](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html#resetting-flash-memory)