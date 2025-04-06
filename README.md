# MICROPYTHON DRIVERS FOR PICOCALC

## KEYBOARD DRIVER IN PYTHON  
Done (tested, work with FBconsole now)

## ILI9488 DRIVER IN C MODULE/PYTHON  
C part has been done for fast 1,2,4,8 bit LUT operation and 16bit 565RGB, frameBuf based swap class in python . 
Now using core1 for framebuff update to screen. Much faster REPL display.

## SPEAKER DRIVER  
N/A

## FUTURE PLAN  
code editor...

## How to use
Hold the boot and plug the usb cable to your raspberry pi pico2/2w. Copy the uf2 file to your raspberry pi pico. Using Thonny to transfer the main.py into the flash disk root. Unplug the usb cable and tune on the power on picocalc. 


FBconsole is a modified version of https://github.com/boochow/FBConsole
