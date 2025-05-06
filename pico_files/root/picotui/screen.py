import os
#import signal
from picocalc import terminal
from .style import picotui_style
class Screen:
    style = picotui_style
    @staticmethod
    def wr(s):
        terminal.wr(s)

    @staticmethod
    def wr_fixedw(s, width):
        # Write string in a fixed-width field
        s = s[:width]
        Screen.wr(s)
        Screen.wr(" " * (width - len(s)))
        # Doesn't work here, as it doesn't advance cursor
        #Screen.clear_num_pos(width - len(s))

    @staticmethod
    def cls():
        Screen.wr("\x1b[2J")

    @staticmethod
    def goto(x, y):
        # TODO: When Python is 3.5, update this to use bytes
        Screen.wr("\x1b[%d;%dH" % (y + 1, x + 1))

    @staticmethod
    def clear_to_eol():
        Screen.wr("\x1b[0K")

    # Clear specified number of positions
    @staticmethod
    def clear_num_pos(num):
        if num > 0:
            Screen.wr("\x1b[%dX" % num)

    @staticmethod
    def attr_color(fg, bg=-1):
        if bg == -1:
            bg = fg >> 4
            fg &= 0xf
        # TODO: Switch to b"%d" % foo when py3.5 is everywhere
        if bg is None:
            if (fg > 8):
                Screen.wr("\x1b[%d;1m" % (fg + 30 - 8))
            else:
                Screen.wr("\x1b[%dm" % (fg + 30))
        else:
            assert bg <= 8
            if (fg > 8):
                Screen.wr("\x1b[%d;%d;1m" % (fg + 30 - 8, bg + 40))
            else:
                Screen.wr("\x1b[%d;%dm" % (fg + 30, bg + 40))

    @staticmethod
    def attr_reset():
        #print("attr_reset")
        Screen.wr("\x1b[0m")
        Screen.attr_color(Screen.style['def_fcolor'], Screen.style['def_bcolor'])
        #Screen.attr_color(0,7)# Reset to default colors for gui(black on white)

    @staticmethod
    def cursor(onoff):
        if onoff:
            Screen.wr("\x1b[?25h")
        else:
            Screen.wr("\x1b[?25l")

    def draw_box(self, left, top, width, height):
        # Use http://www.utf8-chartable.de/unicode-utf8-table.pl
        # for utf-8 pseudographic reference
        bottom = top + height - 1
        self.goto(left, top)
        # "┌"
        self.wr("\xda")
        # "─"
        hor = "\xc4" * (width - 2)
        self.wr(hor)
        # "┐"
        self.wr("\xbf")

        self.goto(left, bottom)
        # "└"
        self.wr("\xc0")
        self.wr(hor)
        # "┘"
        self.wr("\xd9")

        top += 1
        while top < bottom:
            # "│"
            self.goto(left, top)
            self.wr("\xb3")
            self.goto(left + width - 1, top)
            self.wr("\xb3")
            top += 1

    def clear_box(self, left, top, width, height,pattern=" "):
        # doesn't work
        #self.wr("\x1b[%s;%s;%s;%s$z" % (top + 1, left + 1, top + height, left + width))
        s = pattern * width
        bottom = top + height
        while top < bottom:
            self.goto(left, top)
            self.wr(s)
            top += 1

    def dialog_box(self, left, top, width, height, title="", bg_pattern=" "):
        self.clear_box(left + 1, top + 1, width - 2, height - 2,bg_pattern)
        self.draw_box(left, top, width, height)
        if title:
            #pos = (width - len(title)) / 2
            pos = 1
            self.goto(left + pos, top)
            self.wr(title)

    @classmethod
    def init_tty(cls):
        #terminal.wr("\x1b[?7l")
        #terminal.wr("\x1b[0m\x1b[?7l\x1b[?25l\x1b[2J\x1b[H")
        terminal.wr("\x1b[0m\x1b[?7l")

    @classmethod
    def deinit_tty(cls):
        #terminal.wr("\x1b[0m\x1b[?7h\x1b[?25h\x1b[2J\x1b[H")
        terminal.wr("\x1b[0m\x1b[?7h")


    @classmethod
    def enable_mouse(cls):
        # Mouse reporting - X10 compatibility mode
        pass

    @classmethod
    def disable_mouse(cls):
        # Mouse reporting - X10 compatibility mode
        pass

    @classmethod
    def screen_size(cls):
        h,w = terminal.get_screen_size()
        return (w,h)

    # Set function to redraw an entire (client) screen
    # This is called to restore original screen, as we don't save it.
    @classmethod
    def set_screen_redraw(cls, handler):
        cls.screen_redraw = handler

    @classmethod
    def set_screen_resize(cls, handler):
        pass
