# MICROPYTHON DRIVERS FOR PICOCALC

## KEYBOARD DRIVER IN PYTHON  
Done (tested, work with FBconsole now)

## ILI9488 DRIVER IN C MODULE/PYTHON  
C part has been done for fast 1,2,4,8 bit LUT operation and 16bit 565RGB, frameBuf based class in python in progress. swap class done, current it is too slow to work with FBconsole, I will make it update on core 1 for 30fps.

## SPEAKER DRIVER  
N/A

## FUTURE PLAN  
After I got my PicoCalc, I will compile a micropython firmware with REPL redirection to TFT and i2c keyboard and ulab module.
