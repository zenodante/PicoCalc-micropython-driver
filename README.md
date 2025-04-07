# MICROPYTHON DRIVERS FOR PICOCALC




## BUILD
```
Folder structure

|
|-micropython                      //clone micropython folder here
|      |-ports
|         |-rp2
|           |-build               //create folder for build
|           |-modules             //here put fbconsole.py and picocalc.py
|-PicoCalc-micropython-driver     //folder for lcd c driver module
|-Any other modules like ulab, etc. al
```

Build Micropython Normally, While including as user module
```
cd micropython/ports/rp2
git submodule update --init --recursive
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

## CREDITS
FBconsole is a modified version of https://github.com/boochow/FBConsole
