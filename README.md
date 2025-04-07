# MICROPYTHON DRIVERS FOR PICOCALC

## BUILD
Build Micropython Normally, While including as user module
```
cd micropython/ports/rp2
mkdir build && cd build
cmake .. -DUSER_C_MODULES="Location/Of/PicoCalc-micropython-driver/micropython.cmake" -DMICROPY_BOARD=[TARGET BOARD]
```
Target Boards Can Be:
* RPI_PICO
* RPI_PICO2
* RPI_PICO2_W

Others untested.

## INSTALLATION
* Flash UF2 to Pico Normally
* Place Python Files into Pico's Root Directory

(Using Thonny is Easiest)

## FEATURES
#### Keyboard Driver
Done (tested, work with FBconsole now)
#### ILI9488 Driver In C Module/Python  
C part has been done for fast 1,2,4,8 bit LUT operation and 16bit 565RGB, frameBuf based swap class in python . 
Now using core1 for framebuff update to screen. Much faster REPL display.
#### Speaker Driver
N/A

## TODO
Code Editor...


FBconsole is a modified version of https://github.com/boochow/FBConsole
