class Bar:
    def __init__(self, framebuf, color=2, bgcolor=0, thicc=False, subtle=False, flip=False, dispw=320, disph=320):
        self.framebuf = framebuf
        self.color = color
        self.bgcolor = bgcolor
        self.thicc = thicc
        self.subtle = subtle
        self.flip = flip
        self.dispw = dispw
        self.disph = disph
        self.clear()
    def clear(self):
        if self.thicc:
            self.framebuf.rect(self.dispw-2,0,2,self.disph,self.bgcolor)
        else:
            self.framebuf.vline(self.dispw-1,0,self.disph,self.bgcolor)

    def draw(self, value):
        base = self.dispw - (2 if self.thicc else 1)

        full_height = round(self.disph * value / (98 if self.subtle else 100))
        height = min(max(full_height, 0), self.disph)

        if self.flip:
            y_fg = self.disph - height if not self.subtle else max(self.disph - 2, 0)
            y_bg = 0
            bg_h = height if not self.subtle else 0
        else:
            y_fg = self.disph - height if not self.subtle else min(self.disph - 2, self.disph - height)
            y_bg = height if not self.subtle else 0
            bg_h = self.disph - height if not self.subtle else 0

        fg_h = 2 if self.subtle else height

        if self.thicc:
            self.clear()
            self.framebuf.rect(base, y_fg, 2, fg_h, self.color)
        else:
            self.clear()
            self.framebuf.vline(base, y_fg, fg_h, self.color)

        self.framebuf.show()

if __name__ == "__main__":
    from main import *
    import time
    bar = Bar(pc_display, color=2, bgcolor=1, thicc=False, subtle=False, flip=False)
    for i in range(0,101,1):
        bar.draw(i)
        time.sleep_ms(100)
    