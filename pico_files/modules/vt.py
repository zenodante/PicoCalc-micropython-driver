from collections import deque
import uio
import vtterminal
from micropython import const
import time
import os

sc_char_width =  const(53)
sc_char_height =  const(40)

class vt(uio.IOBase):
    

    def __init__(self,framebuf,keyboard,screencaptureKey=0x15,sd=None,captureFolder="/"): #ctrl+U for screen capture
        if not captureFolder.startswith("/"):
            captureFolder = "/"+captureFolder
        if captureFolder.endswith("/"):
            captureFolder = captureFolder[:-1]
        self.captureFolder = captureFolder

        self.framebuf = framebuf
        self.sd = sd
        self.keyboardInput = bytearray(30)
        self.outputBuffer = deque((), 30)
        vtterminal.init(self.framebuf)
        self.keyboard = keyboard
        self.screencaptureKey = screencaptureKey
    
    def screencapture(self):
        if self.sd:
            folder = '/sd'+self.captureFolder
        else:
            folder = self.captureFolder
        self.framebuf.stopRefresh()
        if not folder in os.listdir(folder.rsplit("/", 1)[0]):
            try:
                os.mkdir(folder)
            except OSError:
                self.framebuf.recoverRefresh()
                return
        filename = "{}/screen_{}.raw".format(folder, time.ticks_ms())
        with open(filename, "wb") as f:
            f.write(self.framebuf.buf)
        self.framebuf.recoverRefresh()

        
    def stopRefresh(self):
        self.framebuf.stopRefresh()

    def recoverRefresh(self):
        self.framebuf.recoverRefresh()

    def wr(self,input):
        #print("WR:", repr(input))
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
        while not self.outputBuffer:
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
                #if self.screencaptureKey in self.keyboardInput[:n]:
                #    self.screencapture()
                self.outputBuffer.extend(self.keyboardInput[:n])

        return chr(self.outputBuffer.popleft())
        

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