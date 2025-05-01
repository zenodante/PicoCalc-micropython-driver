import picocalc
from picocalc import PicoDisplay, PicoKeyboard, PicoSD, PicoSpeaker
import os
import vt
import sys
# Separated imports because Micropython is super finnicky
from picocalc_system import run, files, memory, disk

from pye import pye_edit

try:
    pc_display = PicoDisplay(320, 320)
    pc_keyboard = PicoKeyboard()
    # Mount SD card to /sd on boot
    pc_sd = PicoSD()
    pc_sd.mount()
    pcs_L = PicoSpeaker(26)
    pcs_R = PicoSpeaker(27)
    pc_terminal = vt.vt(pc_display, pc_keyboard, sd=pc_sd())
    
    _usb = sys.stdout  # 

    def usb_debug(msg):
        if isinstance(msg, str):
            _usb.write(msg)
        else:
            _usb.write(str(msg))
        _usb.write('\r\n')
    picocalc.usb_debug = usb_debug

    picocalc.display = pc_display
    picocalc.keyboard = pc_keyboard
    picocalc.terminal = pc_terminal
    picocalc.sd = pc_sd

    def edit(*args, tab_size=2, undo=50):
        #dry the key buffer before editing
        pc_terminal.dryBuffer()
        return pye_edit(args, tab_size=tab_size, undo=undo, io_device=pc_terminal)
    picocalc.edit = edit

    os.dupterm(pc_terminal)
    pc_sd.check_mount()
    #usb_debug("boot.py done.")

except Exception as e:
    import sys
    sys.print_exception(e)
    try:
        os.dupterm(None).write(b"[boot.py error]\n")
    except:
        pass
    