from picocalc import PicoDisplay, PicoKeyboard
from fbconsole import FBConsole
import uos
import os
import vt

# Separated imports because Micropython is super finnicky
from picocalc_system import initsd as initsd
from picocalc_system import killsd as killsd

# Mount SD card to /sd on boot

pd = PicoDisplay(320,320)#display
kb = PicoKeyboard()#keyboard
fb=FBConsole( pd, bgcolor=0, fgcolor=2, width=320, height=320,readobj=kb,fontX=6,fontY=8)#fbconsole
te = vt.vt(pd,kb)#terminal
os.dupterm(fb) 

sd = initsd()#sd card
