import framebuf
import picocalcdisplay
from micropython import const
from machine import Pin, I2C
from collections import deque
import time

sd = None
keyboard, display = None, None
terminal = None
edit = None
usb_debug = None

_REG_VER = const(0x01) # fw version
_REG_CFG = const(0x02) # config
_REG_INT = const(0x03) # interrupt status
_REG_KEY = const(0x04) # key status
_REG_BKL = const(0x05) # backlight
_REG_DEB = const(0x06) # debounce cfg
_REG_FRQ = const(0x07) # poll freq cfg
_REG_RST = const(0x08) # reset
_REG_FIF = const(0x09) # fifo
_REG_BK2 = const(0x0A) # backlight 2
_REG_BAT = const(0x0B) # battery
_REG_DIR = const(0x0C) # gpio direction
_REG_PUE = const(0x0D) # gpio input pull enable
_REG_PUD = const(0x0E) # gpio input pull direction
_REG_GIO = const(0x0F) # gpio value
_REG_GIC = const(0x10) # gpio interrupt config
_REG_GIN = const(0x11) # gpio interrupt status
_KEY_COUNT_MASK = const(0x1F)
_WRITE_MASK = const(1 << 7)
_StateIdle = const(0)
_StatePress = const(1)
_StateLongPress = const(2)
_StateRelease = const(3)


class PicoDisplay(framebuf.FrameBuffer):
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
        elif color_type == framebuf.MONO_HMSB:
            self.buffer = bytearray(self.width * self.height//8)


        super().__init__(self.buffer, self.width, self.height, color_type)
        picocalcdisplay.init(self.buffer,color_type,True)

        
    def stopRefresh(self):
        picocalcdisplay.stopAutoUpdate()
    
    def recoverRefresh(self):
        picocalcdisplay.startAutoUpdate()
    
    def text(self,c, x0, y0, color):
        picocalcdisplay.drawTxt6x8(c,x0,y0,color)

    def show(self):
        picocalcdisplay.update()






class PicoKeyboard:
    def __init__(self,sclPin=7,sdaPin=6,address=0x1f):
        self.hardwarekeyBuf = deque((),30)
        self.i2c = I2C(1,scl=Pin(sclPin),sda=Pin(sdaPin),freq=10000)
        #self.i2c.scan()
        self.ignor = True
        self.address = address
        self.temp=bytearray(2)
        self.reset()
        self.isShift = False
        self.isCtrl = False
        self.isAlt = False
    
    def ignor_mod(self):
        self.ignor = True

    def write_cmd(self,cmd):
        self.i2c.writeto(self.address,bytearray([cmd]))

    def read_reg16(self,reg):
        self.temp[0]=reg
        self.i2c.writeto(self.address,self.temp[0:1])
        self.i2c.readfrom_into(self.address,self.temp)
        return self.temp
    
    def read_reg8(self,reg):
        self.i2c.writeto(self.address, bytes(reg)) 
        #self.temp[0]=reg
        #self.i2c.writeto(self.address,self.temp[0:1])
        return self.i2c.readfrom(self.address, 1)[0]
        #self.i2c.readfrom_into(self.address,memoryview(self.temp)[0:1])
        #return self.temp
    
    def write_reg(self,reg,value):
        self.temp[0]=reg| _WRITE_MASK
        self.temp[1]=value
        self.i2c.writeto(self.address,self.temp)

    def enable_report_mods(self):
        currentCFG = self.read_reg8(_REG_CFG)
        self.temp[0]=currentCFG | (0x01<<6)
        self.write_reg(_REG_CFG,self.temp[0:1])
    
    def disable_report_mods(self):
        currentCFG = self.read_reg8(_REG_CFG)
        self.temp[0]=currentCFG & (~(0x01<<6))
        self.write_reg(_REG_CFG,self.temp[0:1])
    
    def enable_use_mods(self):
        currentCFG = self.read_reg8(_REG_CFG)
        self.temp[0]=currentCFG | (0x01<<7)
        self.write_reg(_REG_CFG,self.temp[0:1])

    def disable_use_mods(self):
        currentCFG = self.read_reg8(_REG_CFG)   
        self.temp[0]=currentCFG & (~(0x01<<7))
        self.write_reg(_REG_CFG,self.temp[0:1])

    def reset(self):
        self.write_cmd(_REG_RST)
        time.sleep_ms(100)

    def keyCount(self):
        buf = self.read_reg16(_REG_KEY)
        return (buf[0] & _KEY_COUNT_MASK)

    def keyEvent(self):
        if (self.keyCount() == 0):
            return None
        else:
            buf = self.read_reg16(_REG_FIF)
        return buf
    
    def backlight(self):
        return self.read_reg8(_REG_BKL)
    
    def setBacklight(self,value):
        self.write_reg(_REG_BKL,value)

    def backlight_keyboard(self):
        return self.read_reg8(_REG_BK2)
    
    def setBacklight_keyboard(self,value):
        self.write_reg(_REG_BK2,value)

    def battery(self):
        return self.read_reg16(_REG_BAT)
    
    def readinto(self, buf):
        
        numkeysInhardware = self.keyCount()#how many keys in hardware
        if numkeysInhardware != 0:
            for i in range(numkeysInhardware):
                keyGot=self.keyEvent()
                state = keyGot[0]
                key = keyGot[1]
                if state == _StatePress or state == _StateLongPress:

                    if key == 0xa2 or key == 0xa3:
                        self.isShift = True
                    elif key == 0xa5:
                        self.isCtrl = True
                    elif key == 0xa1:
                        self.isAlt = True              
                    else:
                        #check current shift/ctrl/alt state
                        modifier=b''
                        if self.isShift and self.isAlt and (not self.isCtrl):
                            modifier=b';4'
                        elif self.isShift and self.isCtrl and (not self.isAlt):
                            modifier=b';6'
                        elif self.isAlt and self.isCtrl and (not self.isShift):
                            modifier=b';7'    
                        elif self.isShift and self.isCtrl and self.isAlt:
                            modifier=b';8'    
                        elif self.isAlt and (not self.isCtrl) and (not self.isShift):
                            modifier=b';3'    
                        elif (not self.isAlt) and self.isCtrl and (not self.isShift):
                            modifier=b';5'  
                        elif (not self.isAlt) and (not self.isCtrl) and self.isShift:
                            modifier=b';2'  

                        if key >=0xB4 and key <= 0xB7:
                        #direction keys
                            #self.hardwarekeyBuf.append(0x1b)
                            #self.hardwarekeyBuf.append(ord('['))
                            if modifier != b'':
                                parameters = b'1'
                            else:
                                parameters = b''
                            if key == 0xB4:
                                self.hardwarekeyBuf.extend(b'\x1b['+parameters+modifier+b'D')
                            elif key == 0xB5:
                                self.hardwarekeyBuf.extend(b'\x1b['+parameters+modifier+b'A')
                            elif key == 0xB6:
                                self.hardwarekeyBuf.extend(b'\x1b['+parameters+modifier+b'B')
                            elif key == 0xB7:
                                self.hardwarekeyBuf.extend(b'\x1b['+parameters+modifier+b'C')
                        elif key == 0x0A:
                            self.hardwarekeyBuf.append(ord('\r'))
                            self.hardwarekeyBuf.append(ord('\n')) #return key
                        elif key == 0xB1:  # KEY_ESC
                            self.hardwarekeyBuf.extend(b'\x1b\x1b')
                        elif key == 0xD2: #KEY_HOME
                            self.hardwarekeyBuf.extend(b'\x1b[H')
                        elif key == 0xD5: #end
                            self.hardwarekeyBuf.extend(b'\x1b[F')
                        elif key == 0x08: #backspace
                            self.hardwarekeyBuf.append(0x7F)
                        elif key == 0xD4: #delete
                            self.hardwarekeyBuf.extend(b'\x1b[3'+modifier+b'~')
                        else:
                            if self.isAlt == True:
                                if key !=ord(' ') and key!=ord(',') and key!=ord('.'):
                                    self.hardwarekeyBuf.extend(b'\x1b')#to match the vt100 terminal style
                                    self.hardwarekeyBuf.append(key)
                            elif self.isCtrl == True:   
                                self.hardwarekeyBuf.append(key&0x1F)
                            else:
                                self.hardwarekeyBuf.append(key)
                else:
                    if key == 0xa2 or key == 0xa3:
                        self.isShift = False
                    elif key == 0xa5:
                        self.isCtrl = False
                    elif key == 0xa1:
                        self.isAlt = False   
      
                    
                        
                
                
                
                #self.hardwarekeyBuf.append(key[:])
        #now deside how many keys to send to buf
        requestedkeys = len(buf)
        keysLeft = requestedkeys
        if len(self.hardwarekeyBuf)==0: #after read in the key, still no key in buffer
            return None
        #print("init buf")
        #print(buf)
        #print("hardware key buf size")
        #print(len(self.hardwarekeyBuf))
        while keysLeft > 0:
            
            #fill all keys until key list is empty
            if len(self.hardwarekeyBuf)  == 0:
                break #all keys has been read and process
            
            key = self.hardwarekeyBuf.popleft()#remove the processed key from key list
            buf[-keysLeft]=key
            keysLeft -=1
            
        #print("read buff")   
        #print(buf)
        #print(requestedkeys-keysLeft)
        if requestedkeys-keysLeft == 0:
            return None
        else:
            return (requestedkeys-keysLeft)


        
        

