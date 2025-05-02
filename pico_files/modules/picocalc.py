import framebuf
import picocalcdisplay
from micropython import const
import machine
from machine import Pin, I2C, PWM, SPI
from collections import deque
import time
import sdcard
import uos
import array
from colorer import Fore, Back, Style, print, autoreset
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

'''
import uctypes
from uctypes import struct, OBJ, NATIVE_UINTPTR, UINT16, UINT8, LITTLE_ENDIAN
from uctypes import addressof

W2, H2 = 320, 320
buf2 = bytearray(W2 * H2/2)

# typedef struct _mp_obj_framebuf_t {
#     mp_obj_base_t base;    // offset 0, 4 bytes
#     mp_obj_t      buf_obj; // offset 4, 4 bytes
#     void         *buf;     // offset 8, 4 bytes
#     uint16_t      width;   // offset 12, 2 bytes
#     uint16_t      height;  // offset 14, 2 bytes
#     uint16_t      stride;  // offset 16, 2 bytes
#     uint8_t       format;  // offset 18, 1 byte
# } mp_obj_framebuf_t;
layout = {
    'buf_obj': (OBJ,              4),
    'buf_ptr': (NATIVE_UINTPTR,   8),
    'width':   (UINT16  | LITTLE_ENDIAN, 12),
    'height':  (UINT16  | LITTLE_ENDIAN, 14),
    'stride':  (UINT16  | LITTLE_ENDIAN, 16),
    'format':  (UINT8,            18),
}


fb_s = struct(addressof(display), layout)
fb_s.buf_obj = buf2
fb_s.buf_ptr = addressof(buf2)

#fb_s.width  = W2
#fb_s.height = H2
#fb_s.stride = W2

#fb_s.format = framebuf.GS8



'''
class PicoDisplay(framebuf.FrameBuffer):
    def __init__(self, width, height,color_type = framebuf.GS4_HMSB):
        self.width = width
        self.height = height
        if color_type == framebuf.GS4_HMSB:
            buffer = bytearray(self.width * self.height//2)  # 4bpp mono
        elif color_type == framebuf.RGB565:
            buffer = bytearray(self.width * self.height*2)
        elif color_type == framebuf.GS8:
            buffer = bytearray(self.width * self.height)
        elif color_type == framebuf.GS2_HMSB:
            buffer = bytearray(self.width * self.height//4)
        elif color_type == framebuf.MONO_HMSB:
            buffer = bytearray(self.width * self.height//8)


        super().__init__(buffer, self.width, self.height, color_type)
        picocalcdisplay.init(buffer,color_type,True)

    def restLUT(self):
        picocalcdisplay.resetLUT(0)

    def switchPredefinedLUT(self, name='vt100'):
        if name == 'vt100':
            picocalcdisplay.resetLUT(0)
            
        elif name == 'pico8':
            picocalcdisplay.resetLUT(1)
        else:
            raise ValueError("Unknown LUT name. Use 'vt100' or 'pico8'.")

    def getLUT(self):
        return picocalcdisplay.getLUTview().cast("H")

    def setLUT(self,lut):
        if not (isinstance(lut, array.array)):
            raise TypeError("LUT must be an array of type 'H' (unsigned short)")
        picocalcdisplay.setLUT(lut)

    def stopRefresh(self):
        picocalcdisplay.stopAutoUpdate()
    
    def recoverRefresh(self):
        picocalcdisplay.startAutoUpdate()
    
    def text(self,c, x0, y0, color):
        picocalcdisplay.drawTxt6x8(c,x0,y0,color)

    def show(self,core=1):
        picocalcdisplay.update(core)

    def isScreenUpdateDone(self):
        return picocalcdisplay.isScreenUpdateDone()

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
                            #self.hardwarekeyBuf.append(ord('\n')) #return key
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

class PicoSD:
    """
    Example class for SD card configuration and management by LaikaSpaceDawg.
    This class handles the mounting and unmounting of the SD card, as well as checking its status.
    Also demonstrates basic uColorama usage for colored output.
    """
    def __init__(self, mount_point="/sd", sck_pin=18, mosi_pin=19, miso_pin=16, cs_pin=17, spi_bus=0, baudrate=1000000):
        """
        Initialize SD card configuration.

        :param mount_point: Directory to mount the SD card to.
        :param sck_pin: GPIO pin connected to SCK.
        :param mosi_pin: GPIO pin connected to MOSI.
        :param miso_pin: GPIO pin connected to MISO.
        :param cs_pin: GPIO pin connected to CS.
        :param spi_bus: SPI bus to be used.
        :param baudrate: SPI communication speed.
        """
        self.mount_point = mount_point
        self.sck_pin = sck_pin
        self.mosi_pin = mosi_pin
        self.miso_pin = miso_pin
        self.cs_pin = cs_pin
        self.spi_bus = spi_bus
        self.baudrate = baudrate
        self.sd = None

        # Attempt to mount the SD card on initialization
        self.mount()

    def __call__(self):
        """Allow the SDManager object to be called like a function to get the SDCard object."""
        if self.sd:
            return self.sd
    
    def mount(self):
        """
        Mount the SD card.
        """
        if self.sd is None:
            try:
                self.sd = sdcard.SDCard(
                    machine.SPI(self.spi_bus, baudrate=self.baudrate, polarity=0, phase=0,
                                sck=machine.Pin(self.sck_pin),
                                mosi=machine.Pin(self.mosi_pin),
                                miso=machine.Pin(self.miso_pin)),
                    machine.Pin(self.cs_pin)
                )
                uos.mount(self.sd, self.mount_point)
                print(f"{Fore.GREEN}SD card mounted successfully at", self.mount_point)
            except Exception as e:
                print(f"{Fore.RED}Failed to mount SD card: {e}")
                self.sd = None
        else:
            print(f"{Fore.YELLOW}SD card is already mounted.")

    def unmount(self):
        """
        Unmount the SD card.
        """
        if self.sd is not None:
            try:
                uos.umount(self.mount_point)
                self.sd = None
                print(f"SD card unmounted from {self.mount_point}.")
            except Exception as e:
                print(f"{Fore.RED}Failed to unmount SD card: {e}")
        else:
            print("No SD card is mounted to unmount.")

    def check_mount(self):
        """
        Check if the SD card is mounted.
        """
        try:
            if uos.stat(self.mount_point):
                print(f"{Fore.GREEN}SD card is mounted at {self.mount_point}.")
        except OSError:
            print(f"{Fore.RED}No SD card is mounted at {self.mount_point}.")

# Frequency definitions for musical notes
NOTE_FREQUENCIES = {
    'B1': 31, 'C2': 33, 'CS2': 35, 'D2': 37, 'DS2': 39, 'E2': 41, 'F2': 44, 'FS2': 46,
    'G2': 49, 'GS2': 52, 'A2': 55, 'AS2': 58, 'B2': 62, 'C3': 65, 'CS3': 69, 'D3': 73,
    'DS3': 78, 'E3': 82, 'F3': 87, 'FS3': 93, 'G3': 98, 'GS3': 104, 'A3': 110, 'AS3': 117,
    'B3': 123, 'C4': 131, 'CS4': 139, 'D4': 147, 'DS4': 156, 'E4': 165, 'F4': 175,
    'FS4': 185, 'G4': 196, 'GS4': 208, 'A4': 220, 'AS4': 233, 'B4': 247, 'C5': 262,
    'CS5': 277, 'D5': 294, 'DS5': 311, 'E5': 330, 'F5': 349, 'FS5': 370, 'G5': 392,
    'GS5': 415, 'A5': 440, 'AS5': 466, 'B5': 494, 'C6': 523, 'CS6': 554, 'D6': 587,
    'DS6': 622, 'E6': 659, 'F6': 698, 'FS6': 740, 'G6': 784, 'GS6': 831, 'A6': 880,
    'AS6': 932, 'B6': 988, 'C7': 1047, 'CS7': 1109, 'D7': 1175, 'DS7': 1245, 'E7': 1319,
    'F7': 1397, 'FS7': 1480, 'G7': 1568, 'GS7': 1661, 'A7': 1760, 'AS7': 1865, 'B7': 1976,
    'C8': 2093, 'CS8': 2217, 'D8': 2349, 'DS8': 2489, 'E8': 2637, 'F8': 2794, 'FS8': 2960,
    'G8': 3136, 'GS8': 3322, 'A8': 3520, 'AS8': 3729, 'B8': 3951, 'C9': 4186, 'CS9': 4435,
    'D9': 4699, 'DS9': 4978, 'P': 0  # 'P' is for pause
}

class PicoSpeaker:
    def __init__(self, pin_number):
        self.buzzer_pin = Pin(pin_number)
        self.pwm = None

    def tone(self, tone, duration):
        """
        Play a tone given by a note string from NOTE_FREQUENCIES or directly as a frequency number.
        
        :param tone: Either a note string ("A4", "C5", etc.) or a frequency in Hz.
        :param duration: Duration in seconds for which to play the tone.
        Written by @LaikaSpaceDawg (https://github.com/LaikaSpaceDawg/PicoCalc-micropython)
        """
        frequency = 0
        
        if isinstance(tone, str) and tone.upper() in NOTE_FREQUENCIES:
            frequency = NOTE_FREQUENCIES[tone.upper()]
        elif isinstance(tone, (int, float)):
            frequency = tone
            
        if frequency > 0:
            self.pwm = PWM(self.buzzer_pin)
            self.pwm.freq(frequency)
            self.pwm.duty_u16(32768)
            time.sleep(duration * 0.9)
        if self.pwm:
            self.pwm.deinit()
        time.sleep(duration * 0.1)

    def tones(self, notes_durations):
        """
        Play a sequence of notes with their respective durations.
        
        :param notes_durations: List of tuples where each tuple contains a note and its duration.
                                e.g., [("A4", 0.5), ("C5", 0.5)]
        """
        for tone, duration in notes_durations:
            self.tone(tone, duration)

    def rtttl(self, text):
        """ 
        Convert RTTTL formatted string into frequency-duration pairs. 
        Provided by: @GraphicHealer (https://github.com/GraphicHealer/MicroPython-RTTTL)
        """
        try:
            title, defaults, song = text.split(':')
            d, o, b = defaults.split(',')
            d = int(d.split('=')[1])
            o = int(o.split('=')[1])
            b = int(b.split('=')[1])
            whole = (60000 / b) * 4
            noteList = song.split(',')
        except:
            return 'Please enter a valid RTTTL string.'

        notes = 'abcdefgp'
        outList = []

        for note in noteList:
            index = 0
            for i in note:
                if i in notes:
                    index = note.find(i)
                    break

            length = note[0:index]
            value = note[index:].replace('#', 's').replace('.', '')

            if not any(char.isdigit() for char in value):
                value += str(o)
            if 'p' in value:
                value = 'p'

            if length == '':
                length = d
            else:
                length = int(length)

            length = whole / length

            if '.' in note:
                length += length / 2

            outList.append((NOTE_FREQUENCIES[value.upper()], length))

        return outList

    def play_rtttl(self, rtttl_string):
        """
        Play RTTTL formatted song.
        Provided by: @GraphicHealer (https://github.com/GraphicHealer/MicroPython-RTTTL)
        """
        tune = self.rtttl(rtttl_string)

        if type(tune) is not list:
            print(tune)
            return

        for freqc, msec in tune:
            self._play_frequency(freqc, msec * 0.001)