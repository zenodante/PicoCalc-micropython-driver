class IO_DEVICE:
    def __init__(self, terminal,Editor):
        self.terminal = terminal

        Editor.KEYMAP["\x08"] = 0x08

        try:
            from micropython import kbd_intr

            kbd_intr(-1)
        except ImportError:
            pass

    def wr(self, s):
        self.terminal.write(s)

    def rd(self):
        return self.terminal.read(1)

    def rd_raw(self):  ## just to have it implemented
        return self.rd()

    def deinit_tty(self):
        
        try:
            from micropython import kbd_intr

            kbd_intr(3)
        except ImportError:
            pass

    def get_screen_size(self):
        return self.terminal.getScreenSize()

