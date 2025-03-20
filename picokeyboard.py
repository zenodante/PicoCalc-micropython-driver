from micropython import const
from machine import Pin, I2C
import time

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


class PicoKeyboard:
    def __init__(self,sclPin=7,sdaPin=6,address=0x1f):
        self.hardwarekeyBuf = list()
        self.i2c = I2C(1,scl=Pin(sclPin),sda=Pin(sdaPin),freq=10000)
        #self.i2c.scan()
        self.address = address
        self.temp=bytearray(2)
        self.reset()


    def write_cmd(self,cmd):
        self.i2c.writeto(self.address,bytearray([cmd]))

    def read_reg16(self,reg):
        self.temp[0]=reg
        self.i2c.writeto(self.address,self.temp[0:1])
        self.i2c.readfrom_into(self.address,self.temp)
        return self.temp
    
    def read_reg8(self,reg):
        self.temp[0]=reg
        self.i2c.writeto(self.address,self.temp[0:1])
        self.i2c.readfrom_into(self.address,self.temp[0:1])
        return self.temp[0]
    
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
        return (buf[1] & _KEY_COUNT_MASK)

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
        return self.read_reg8(_REG_BAT)
    
    def readinto(self, buf, nbytes=0):
        numkeysInhardware = self.keyCount()#how many keys in hardware
        if numkeysInhardware != 0:
            while numkeysInhardware > 0:#read all keys from hardware
                key = self.keyEvent()
                self.hardwarekeyBuf.append(key)
                numkeysInhardware -= 1
        #now deside how many keys to send to buf
        if nbytes == 0:
            requestedkeys = len(buf)
        else:
            requestedkeys = min(nbytes,len(buf))
        if len(self.hardwarekeyBuf)==0: #after read in the key, still no key in buffer
            return None

        while requestedkeys > 0:
            #fill all keys until key list is empty
            if len(self.hardwarekeyBuf)  == 0:
                break #all keys has been read and process
            state = self.hardwarekeyBuf[0][0]
            key = self.hardwarekeyBuf[0][1]
            if state == _StatePress or state == _StateLongPress:
                if key >=0xB4 and key <= 0xB7:
                    #direction keys
                    if requestedkeys >= 3:#still have enough space in buf
                        
                        buf[-requestedkeys] = '\x1b'
                        buf[-requestedkeys+1] = '['
                        if key == 0xB4:
                            buf[-requestedkeys+2] = 'D'
                        elif key == 0xB5:
                            buf[-requestedkeys+2] = 'A'
                        elif key == 0xB6:
                            buf[-requestedkeys+2] = 'B'
                        elif key == 0xB7:
                            buf[-requestedkeys+2] = 'C'
                        requestedkeys -= 3                       
                    else:
                        #no enough space in buf
                        break
                else:
                    #self.hardwarekeyBuf.pop(0) 
                    if key == 0x0A:
                        buf[-requestedkeys] = '\n' #return key
                    elif key == 0xB1:  # KEY_ESC
                        buf[-requestedkeys] = '\x1b'
                    elif key == 0x08 or key == 0xD4: #backspace and del
                        buf[-requestedkeys] = '\x7F'
                    else:
                        buf[-requestedkeys] = key
                    requestedkeys -= 1
            
            self.hardwarekeyBuf.pop(0) #remove the processed key from key list
            

        return (len(buf) - requestedkeys)


        
        