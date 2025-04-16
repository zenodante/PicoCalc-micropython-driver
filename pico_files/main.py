from picocalc import PicoDisplay, PicoKeyboard
from fbconsole import FBConsole
import os
import vt
import builtins
import sys
# Separated imports because Micropython is super finnicky
from picocalc_system import initsd as initsd
from picocalc_system import killsd as killsd

# Mount SD card to /sd on boot

builtins.pc_display = PicoDisplay(320,320)#display
builtins.pc_keyboard = PicoKeyboard()#keyboard
fb=FBConsole( builtins.pc_display , bgcolor=0, fgcolor=2, width=320, height=320,readobj=builtins.pc_keyboard ,fontX=6,fontY=8)#fbconsole
builtins.pc_sd = initsd()#sd card
builtins.pc_terminal = vt.vt(builtins.pc_display,builtins.pc_keyboard,sd=builtins.pc_sd)#terminal

_usb = sys.stdin

def usb_debug(msg):
    if isinstance(msg, str):
        _usb.write(msg)
    else:
        _usb.write(str(msg))
    _usb.write('\r\n')

builtins.usb_debug = usb_debug
os.dupterm(fb) 


#we may move all the init to boot.py later, but for now we want to keep it in main.py for testing purposes