import sys
import machine
import os

import picocalc
from picocalc import PicoDisplay, PicoKeyboard, PicoSD, PicoSpeaker
import vt
from battery import Bar
from clock import PicoRTC
# Separated imports because Micropython is super finnicky
from picocalc_sys import clear, run, files, memory, disk

from eigenmath import EigenMath as em
from pye import pye_edit

from colorer import Fore, Back, Style, print, autoreset
autoreset(True)

terminal_rows = 40
terminal_width = 53
non_scrolling_lines = 2

# Show menu bar?
show_bar = True
index = sys.version.find('MicroPython v')
if index != -1:
    MICROPYTHON_VERSION = sys.version[index + 13:].split()[0]

try:
    machine.freq(200000000)
except:
    pass

def initialize_terminal():
    global non_scrolling_lines, terminal_rows
    print(f"\033[{non_scrolling_lines + 1};{terminal_rows}r", end='')
    
try:
    if show_bar:
        initialize_terminal()
    pc_rtc = PicoRTC()
    pc_rtc.sync()
    pc_display = PicoDisplay(320, 320)
    pc_keyboard = PicoKeyboard()
    # Mount SD card to /sd on boot
    pc_sd = PicoSD()
    pc_sd.mount()
    # Activate both speakers on boot.
    pc_speaker_L = PicoSpeaker(26)
    pc_speaker_R = PicoSpeaker(27)
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

    def edit(*args, tab_size=4, undo=50):
        #dry the key buffer before editing
        pc_terminal.dryBuffer()
        picocalc.editing = True
        return pye_edit(args, tab_size=tab_size, undo=undo, io_device=pc_terminal)
    picocalc.edit = edit

    os.dupterm(pc_terminal)
    print("\n")
    
    def print_header():
        if not picocalc.editing:
            description = f"PicoCalc MicroPython (ver {MICROPYTHON_VERSION})"
            battery = picocalc.keyboard.battery()
            current_time = pc_rtc.time()

            left_text = f"Battery: {battery}%"
            right_text = f"{current_time}"

            padding_left_line1 = ' ' * ((terminal_width - len(description)) // 2)
            padding_right_line1 = ' ' * (terminal_width - len(padding_left_line1) - len(description))
            line1 = f"{Style.FLASHING}{padding_left_line1}{description}{padding_right_line1}"
            # Flashing isnt supported anyway, highlights nicely though
            padding_between_left_right_line2 = ' ' * (terminal_width - len(left_text) - len(right_text))
            line2 = f"{Style.FLASHING}{left_text}{padding_between_left_right_line2}{right_text}"


            print("\0337", end='')  # Save cursor and attributes

            # Print header
            print(f"\033[1;1H{line1}", end='')   # Header line 1
            print(f"\033[2;1H{line2}", end='')   # Header line 2
            # print(f"\033[3;1H{"="*terminal_width}", end='')  # Adjust the position as needed

            # Restore cursor position
            print("\0338", end='')
        
    def update_header(timer=None):
        print_header()
    
    if show_bar:
        print_header()
        header_timer = machine.Timer()
        header_timer.init(mode=machine.Timer.PERIODIC, period=5000, callback=update_header)
        
    pc_sd.check_mount()
    print(f"{Fore.GREEN}Current Time and Date: {pc_rtc.time()}")
    #usb_debug("boot.py done.")

except Exception as e:
    import sys
    sys.print_exception(e)
    try:
        os.dupterm(None).write(b"[boot.py error]\n")
    except:
        pass
    