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
    def __init__(self):
        self.reset()

    def reset(self):
        self.state = 'IDLE'
        self.buffer = bytearray()

    def feed(self, byte):
        self.buffer.append(byte)

        if self.state == 'IDLE':
            if byte == 0x1b:
                self.state = 'ESC'
                return None
            else:
                out = bytes(self.buffer)
                self.reset()
                return out

        elif self.state == 'ESC':
            if byte == ord('['):
                self.state = 'CSI'
                return None
            elif byte == ord('O'):
                self.state = 'SS3'
                return None
            elif byte == 0x1b:
                out = b'\x1b\x1b'
                self.reset()
                return out
            else:
                out = bytes(self.buffer)
                self.reset()
                return out

        elif self.state == 'CSI':
            if byte in range(0x40, 0x7e):  # '@' to '~'
                out = bytes(self.buffer)
                self.reset()
                return out
            return None  # More to come (e.g. ~)

        elif self.state == 'SS3':
            if byte in b'PQRSHF':
                out = bytes(self.buffer)
                self.reset()
                return out
            return None

        else:
            self.reset()
            return None
        
class Widget(Screen):

    def __init__(self):
        self.parser = VT100Parser()
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
            b = terminal.rd()  # Blocking read, returns byte or bytes
            b = b.encode()
            for byte in b:
                result = self.parser.feed(byte)
                if result:
                    return _KEYMAP.get(result, result) 


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
