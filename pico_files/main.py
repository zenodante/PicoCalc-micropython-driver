from picocalc import PicoDisplay, PicoKeyboard
import os
import vt
import sys
# Separated imports because Micropython is super finnicky
from picocalc_system import initsd as initsd
from picocalc_system import killsd as killsd
from pye import pye_edit
# Mount SD card to /sd on boot

pc_display = PicoDisplay(320,320)#display
pc_keyboard = PicoKeyboard()#keyboard
sd = initsd()#sd card
pc_terminal = vt.vt(pc_display,pc_keyboard,sd=sd)#terminal

_usb = sys.stdin

def usb_debug(msg):
    if isinstance(msg, str):
        _usb.write(msg)
    else:
        _usb.write(str(msg))
    _usb.write('\r\n')

def edit(*args, tab_size=2, undo=50):
    ret = pye_edit(args, tab_size=tab_size, undo=undo, io_device=pc_terminal)
    return ret

os.dupterm(pc_terminal) 


#we may move all the init to boot.py later, but for now we want to keep it in main.py for testing purposes