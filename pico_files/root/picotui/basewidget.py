import os

from .screen import Screen
from .defs import KEYMAP as _KEYMAP
from picocalc import terminal
from micropython import const
# Standard widget result actions (as return from .loop())
ACTION_OK = const(1000)
ACTION_CANCEL = const(1001)
ACTION_NEXT = const(1002)
ACTION_PREV = const(1003)


class VT100Parser:
    state = 'IDLE'
    buffer = bytearray(5)  # 
    pos = 0
    
    # 
    KEY_UP = const(1)
    KEY_DOWN = const(2)
    KEY_LEFT = const(3)
    KEY_RIGHT = const(4)
    KEY_HOME = const(5)
    KEY_END = const(6)
    KEY_PGUP = const(7)
    KEY_PGDN = const(8)
    KEY_QUIT = const(9)
    KEY_ENTER = const(10)
    KEY_BACKSPACE = const(11)
    KEY_DELETE = const(12)
    KEY_TAB = b"\t"
    KEY_SHIFT_TAB = const(13)  # 
    KEY_ESC = const(20)
    KEY_F1 = const(30)
    KEY_F2 = const(31)
    KEY_F3 = const(32)
    KEY_F4 = const(33)
    KEY_F5 = const(34)  # 
    KEY_F6 = const(35)  # 
    KEY_F7 = const(36)  # 
    KEY_F8 = const(37) # 
    KEY_F9 = const(38)  # 
    KEY_F10 = const(39)  # 

    @classmethod
    def reset(cls):
        cls.state = 'IDLE'
        cls.pos = 0  # 
    
    @classmethod
    def feed(cls, byte):
        if cls.pos < len(cls.buffer):
            cls.buffer[cls.pos] = byte
            cls.pos += 1
        else:
            cls.reset()
            return None
        
        if cls.state == 'IDLE':
            if byte == 0x1b:  # ESC
                cls.state = 'ESC'
                return None
            elif byte == 0x03:  # Ctrl+C
                cls.reset()
                return cls.KEY_QUIT
            elif byte == 0x0D:  # CR
                cls.reset()
                return cls.KEY_ENTER
            elif byte == 0x7F:  # BACKSPACE
                cls.reset()
                return cls.KEY_BACKSPACE
            elif byte == 0x09:  # TAB
                cls.reset()
                return cls.KEY_TAB
            else:
                # 
                out = chr(byte)
                cls.reset()
                return out
                
        elif cls.state == 'ESC':
            if byte == ord('['):
                cls.state = 'CSI'
                return None
            elif byte == ord('O'):
                cls.state = 'SS3'
                return None
            elif byte == 0x1b:  # 
                cls.reset()
                return cls.KEY_ESC
            else:
                # 
                cls.reset()
                return None
                
        elif cls.state == 'CSI':
            if cls.pos == 3:  # ESC [ X
                if cls.buffer[2] == ord('A'):  # UP
                    cls.reset()
                    return cls.KEY_UP
                elif cls.buffer[2] == ord('B'):  # DOWN
                    cls.reset()
                    return cls.KEY_DOWN
                elif cls.buffer[2] == ord('C'):  # RIGHT
                    cls.reset()
                    return cls.KEY_RIGHT
                elif cls.buffer[2] == ord('D'):  # LEFT
                    cls.reset()
                    return cls.KEY_LEFT
                elif cls.buffer[2] == ord('H'):  # HOME
                    cls.reset()
                    return cls.KEY_HOME
                elif cls.buffer[2] == ord('F'):  # END
                    cls.reset()
                    return cls.KEY_END
                elif cls.buffer[2] == ord('Z'):  # SHIFT+TAB
                    cls.reset()
                    return cls.KEY_SHIFT_TAB
            elif cls.pos == 4:  # ESC [ n ~
                if cls.buffer[2] == ord('3') and cls.buffer[3] == ord('~'):  # DELETE
                    cls.reset()
                    return cls.KEY_DELETE
                elif cls.buffer[2] == ord('4') and cls.buffer[3] == ord('~'):  # END (some terminals)
                    cls.reset()
                    return cls.KEY_END
                elif cls.buffer[2] == ord('5') and cls.buffer[3] == ord('~'):  # PGUP
                    cls.reset()
                    return cls.KEY_PGUP
                elif cls.buffer[2] == ord('6') and cls.buffer[3] == ord('~'):  # PGDN
                    cls.reset()
                    return cls.KEY_PGDN
            elif cls.pos == 5:  # ESC [ nn ~
                if cls.buffer[2] == ord('1') and cls.buffer[3] == ord('5') and cls.buffer[4] == ord('~'):  # F5
                    cls.reset()
                    return cls.KEY_F5
                elif cls.buffer[2] == ord('1') and cls.buffer[3] == ord('7') and cls.buffer[4] == ord('~'):  # F6
                    cls.reset()
                    return cls.KEY_F6
                elif cls.buffer[2] == ord('1') and cls.buffer[3] == ord('8') and cls.buffer[4] == ord('~'):  # F7
                    cls.reset()
                    return cls.KEY_F7
                elif cls.buffer[2] == ord('1') and cls.buffer[3] == ord('9') and cls.buffer[4] == ord('~'):  # F8
                    cls.reset()
                    return cls.KEY_F8
                elif cls.buffer[2] == ord('2') and cls.buffer[3] == ord('0') and cls.buffer[4] == ord('~'):  # F9
                    cls.reset()
                    return cls.KEY_F9
                elif cls.buffer[2] == ord('2') and cls.buffer[3] == ord('1') and cls.buffer[4] == ord('~'):  # F10
                    cls.reset()
                    return cls.KEY_F10
            
            # 
            if 0x40 <= byte <= 0x7E:
                cls.reset()
                return None
            return None
            
        elif cls.state == 'SS3':
            if cls.pos == 3:
                if cls.buffer[2] == ord('P'):  # F1
                    cls.reset()
                    return cls.KEY_F1
                elif cls.buffer[2] == ord('Q'):  # F2
                    cls.reset()
                    return cls.KEY_F2
                elif cls.buffer[2] == ord('R'):  # F3
                    cls.reset()
                    return cls.KEY_F3
                elif cls.buffer[2] == ord('S'):  # F4
                    cls.reset()
                    return cls.KEY_F4
                elif cls.buffer[2] == ord('H'):  # HOME (some terminals)
                    cls.reset()
                    return cls.KEY_HOME
                elif cls.buffer[2] == ord('F'):  # END (some terminals)
                    cls.reset()
                    return cls.KEY_END
            
            # 
            cls.reset()
            return None
        
        else:
            # 
            cls.reset()
            return None

        
class Widget(Screen):

    def __init__(self):
        #self.parser = VT100Parser()
        self.kbuf = b""
        self.signals = {}

    def set_xy(self, x, y):
        self.x = x
        self.y = y

    def inside(self, x, y):
        return self.y <= y < self.y + self.h and self.x <= x < self.x + self.w

    def signal(self, sig):
        if sig in self.signals:
            self.signals[sig](self)

    def on(self, sig, handler):
        self.signals[sig] = handler

    @staticmethod
    def longest(items):
        if not items:
            return 0
        return max((len(t) for t in items))

    def set_cursor(self):
        # By default, a widget doesn't use text cursor, so disables it
        self.cursor(False)

    def get_input(self):
        while True:
            ch = terminal.rd()  # e.g. returns '\x1b'
            byte = ord(ch)      # convert to integer 0-255
            result = VT100Parser.feed(byte)
            if result:
                #return _KEYMAP.get(result, result)
                return result


    def handle_input(self, inp):
        if isinstance(inp, list):
            res = self.handle_mouse(inp[0], inp[1])
        else:
            res = self.handle_key(inp)
        return res

    def loop(self):
        self.redraw()
        while True:
            key = self.get_input()
            if key is None:
                continue
            res = self.handle_input(key)

            if res is not None and res is not True:
                return res


class FocusableWidget(Widget):
    # If set to non-False, pressing Enter on this widget finishes
    # dialog, with Dialog.loop() return value being this value.
    finish_dialog = False


class EditableWidget(FocusableWidget):

    def get(self):
        raise NotImplementedError


class ChoiceWidget(EditableWidget):

    def __init__(self, choice):
        super().__init__()
        self.choice = choice

    def get(self):
        return self.choice


# Widget with few internal selectable items
class ItemSelWidget(ChoiceWidget):

    def __init__(self, items):
        super().__init__(0)
        self.items = items

    def move_sel(self, direction):
        self.choice = (self.choice + direction) % len(self.items)
        self.redraw()
        self.signal("changed")
