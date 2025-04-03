import framebuf
import picocalcdisplay
class picoDisplaySwap(framebuf.FrameBuffer):
    def __init__(self, width, height,color_type = framebuf.GS4_HMSB):
        self.width = width
        self.height = height
        if color_type == framebuf.GS4_HMSB:
            self.buffer = bytearray(self.width * self.height//2)  # 4bpp mono
        elif color_type == framebuf.RGB565:
            self.buffer = bytearray(self.width * self.height*2)
        elif color_type == framebuf.GS8:
            self.buffer = bytearray(self.width * self.height)
        elif color_type == framebuf.GS2_HMSB:
            self.buffer = bytearray(self.width * self.height//4)
        elif color_type == framebuf.MONO_HMSB
            self.buffer = bytearray(self.width * self.height//8)


        super().__init__(self.buffer, self.width, self.height, color_type)
        picocalcdisplay.init()

        

    

    def show(self):
        picocalcdisplay.update(self.buffer)
