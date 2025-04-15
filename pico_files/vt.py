from collections import deque
import uio
import vtterminal
from micropython import const

sc_char_width =  const(53)
sc_char_height =  const(40)

class vt(uio.IOBase):
    

    def __init__(self,framebuf,keyboard):
        self.keyboardInput = bytearray(30)
        self.outputBuffer = deque((), 30)
        vtterminal.init(framebuf)
        self._keyboard = keyboard
    
    def wr(self,input):
        for c in input:
            if ord(c) == 0x07:
                pass
            else:
                vtterminal.printChar(ord(c))
        return len(input)
    
    def write(self, buf):    
        return self.wr(buf.decode())
    
    def get_screen_size(self):
        return[sc_char_height,sc_char_width]
    
    def rd(self):

        s = vtterminal.read()
        if s:
            try:
                self.outputBuffer.extend(ord(ch) for ch in s)
            except TypeError:
                raise ValueError("vtterminal.read() must return str")
            except ValueError:
                raise ValueError("Non-ASCII character in vtterminal.read()")


        n = self.keyboard.readinto(self.keyboardInput)
        if n:
            self.outputBuffer.extend(self.keyboardInput[:n])  

        if self.outputBuffer:
            return self.outputBuffer.popleft()
        else:
            return None
        

    def rd_raw(self):
        return self.rd()
    
    def readinto(self, buf):
        s = vtterminal.read()
        if s:
            try:
                self.outputBuffer.extend(ord(ch) for ch in s)
            except TypeError:
                raise ValueError("vtterminal.read() must return str")
            except ValueError:
                raise ValueError("Non-ASCII character in vtterminal.read()")
        n = self.keyboard.readinto(self.keyboardInput)
        if n:
            self.outputBuffer.extend(self.keyboardInput[:n])   
        count = 0
        buf_len = len(buf)
        for i in range(buf_len):
            if self.outputBuffer:
                buf[i] = self.outputBuffer.popleft()
                count += 1
            else:
                break
        return count if count > 0 else None