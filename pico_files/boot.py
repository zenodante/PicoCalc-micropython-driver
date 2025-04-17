from picocalc import PicoDisplay, PicoKeyboard
import os
import vt
import sys
# Separated imports because Micropython is super finnicky
from picocalc_system import initsd as initsd
from picocalc_system import killsd as killsd
from pye import pye_edit
import builtins
# Mount SD card to /sd on boot


try:
    pc_display = PicoDisplay(320, 320)
    pc_keyboard = PicoKeyboard()
    sd = initsd()
    pc_terminal = vt.vt(pc_display, pc_keyboard, sd=sd)
    
    _usb = sys.stdout  # 

    def usb_debug(msg):
        if isinstance(msg, str):
            _usb.write(msg)
        else:
            _usb.write(str(msg))
        _usb.write('\r\n')
    builtins.usb_debug = usb_debug

    builtins.pc_display = pc_display
    builtins.pc_keyboard = pc_keyboard
    builtins.pc_terminal = pc_terminal
    builtins.sd = sd

    def edit(*args, tab_size=2, undo=50):
        return pye_edit(args, tab_size=tab_size, undo=undo, io_device=pc_terminal)
    builtins.edit = edit

    os.dupterm(pc_terminal)

    #usb_debug("boot.py done.")

except Exception as e:
    import sys
    sys.print_exception(e)
    try:
        os.dupterm(None).write(b"[boot.py error]\n")
    except:
        pass