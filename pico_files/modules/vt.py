from collections import deque
import uio
import vtterminal
from micropython import const
import time
import uos

sc_char_width =  const(53)
sc_char_height =  const(40)

def ensure_nested_dir(path):
    parts = path.split("/")
    current = ""
    for part in parts:
        if not part:
            continue
        current = current + "/" + part if current else part
        try:
            uos.stat(current)
        except OSError:
            uos.mkdir(current)



class vt(uio.IOBase):
    

    def __init__(self,framebuf,keyboard,screencaptureKey=0x15,sd=None,captureFolder="/"): #ctrl+U for screen capture
        if sd != None:
            if not captureFolder.startswith("/"):
                captureFolder = "/"+captureFolder
            captureFolder = '/sd'+captureFolder
            if not captureFolder.endswith("/"):
                captureFolder = captureFolder+"/"
            self.captureFolder = captureFolder
            ensure_nested_dir(self.captureFolder)
            
        self.framebuf = framebuf
        self.sd = sd
        self.keyboardInput = bytearray(30)
        self.outputBuffer = deque((), 30)
        vtterminal.init(self.framebuf)
        self.keyboard = keyboard
        self.screencaptureKey = screencaptureKey
    
    def screencapture(self):
        if self.sd:
            filename = "{}screen_{}.raw".format(self.captureFolder, time.ticks_ms())
            with open(filename, "wb") as f:
                f.write(self.framebuf.buffer)
            return True
        return False

    def dryBuffer(self):
        self.outputBuffer = deque((), 30)

        
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
    
    def _updateInternalBuffer(self):
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
            keys = bytes(self.keyboardInput[:n])
            if self.screencaptureKey in keys:
                self.screencapture()
            self.outputBuffer.extend(self.keyboardInput[:n])

    def rd(self):
        while not self.outputBuffer:
            self._updateInternalBuffer()

        return chr(self.outputBuffer.popleft())
        

    def rd_raw(self):
        return self.rd()
    
    def readinto(self, buf):
        self._updateInternalBuffer()
        count = 0
        buf_len = len(buf)
        for i in range(buf_len):
            if self.outputBuffer:
                buf[i] = self.outputBuffer.popleft()
                count += 1
            else:
                break
        return count if count > 0 else None
