from micropython import const
import array
from machine import Timer
from collections import deque
import uio

clBlack =  const(0)
clRed =    const(1)
clGreen =  const(2)
clYellow = const(3)
clBlue =   const(4)
clMagenta =const(5)
clCyan =   const(6)
clWhite =  const(7)


NONE = const(0)
ES = const(1)
CSI = const(2)
CSI2 = const(3)
LSC = const(4)
G0S = const(5)
G1S = const(6)


Bold   =const(0)
Faint  =const(1)
Italic =const(2)
Underline =const(3)
Blink =const(4) 
RapidBlink =const(5)
Reverse =const(6)
Conceal =const(7)

Reserved2  = const(0)
Reserved4  = const(1)
Reserved12 = const(2)
CrLf  = const(3)
Reserved33 = const(4)
Reserved34 = const(5)

EX_Reserved1   = const(0)    
EX_Reserved2  = const(1)
EX_Reserved3  = const(2)
EX_Reserved4  = const(3)
EX_ScreenReverse = const(4)
EX_Reserved6 = const(5)
EX_WrapLine   = const(6)
EX_Reserved8  = const(7)
EX_Reserved9  = const(8)

defaultModeEx = const(0b0000000001000000)
defaultMode = const(0b00001000)
defaultAttr = const(0b00000000)
defaultColor = const((clBlack<<4)|clWhite)

def bit_is_set(value, bitpos):
    return (value >> bitpos) & 1 == 1
def bit_set(value, bitpos, flag):
    if flag:
        return value | (1 << bitpos)
    else:
        return value & ~(1 << bitpos)

class vtterminal(uio.IOBase):

    def __init__(self,fb,inputIO,ch_w=6,ch_h=8,sc_w = 53,sc_h=40):
        self.keyBuf = bytearray(30)
        self.outputBuff = deque((),30)
        self.timer = Timer()
        self.fb = fb
        self.inputIO = inputIO
        self.CH_W = ch_w #char width
        self.CH_H = ch_h #char height
        self.SC_W = sc_w  #screen width in char
        self.SC_H = sc_h #screen height  in char
        self.M_TOP = 0 # top row number
        self.M_BOTTOM = self.SC_H -1 #bottom row number

        self.SCSIZE   = self.SC_W * self.SC_H  
        self.SP_W     = self.SC_W * self.CH_W  
        self.SP_H     = self.SC_H * self.CH_H  
        self.MAX_CH_X = self.CH_W - 1     
        self.MAX_CH_Y = self.CH_H - 1     
        self.MAX_SC_X = self.SC_W - 1     
        self.MAX_SC_Y = self.SC_H - 1    
        self.MAX_SP_X = self.SP_W - 1   
        self.MAX_SP_Y = self.SP_H - 1
        self.screen=bytearray(self.SCSIZE)
        self.attrib=bytearray(self.SCSIZE)     
        self.colors=bytearray(self.SCSIZE) 
        self.tabs=bytearray(self.SC_W)

        self.escMode = NONE
        self.isShowCursor = False
        self.canShowCursor = True
        #self.lastShowCursor = False
        self.hasParam = False
        self.isDECPrivateMode = False
        self.mode = defaultMode
        self.mode_ex = defaultModeEx
        self.p_XP = 0
        self.p_YP = 0

        self.XP = 0
        self.YP = 0
        self.cAttr = defaultAttr
        self.cColor = defaultColor

        self.b_XP = 0
        self.b_YP = 0
        self.bAttr = defaultAttr
        self.bColor = defaultColor

        self.nVals = 0
        self.vals=array.array('h', [0] * 10)

        self.escSwitch ={
            ord('7'):lambda:self.saveCursor(),
            ord('8'):lambda:self.restoreCursor(),
            ord('='):lambda:self.keypadApplicationMode(),
            ord('>'):lambda:self.keypadNumericMode(),
            ord('D'):lambda:self.index(1),
            ord('E'):lambda:self.nextLine(),
            ord('H'):lambda:self.horizontalTabulationSet(),
            ord('M'):lambda:self.reverseIndex(1),
            ord('Z'):lambda:self.identify(),
            ord('c'):lambda:self.resetToInitialState(),
        }
        self.LSCSwitch = {
            ord('3'):lambda:self.doubleHeightLine_TopHalf(),
            ord('4'):lambda:self.doubleHeightLine_BotomHalf(),
            ord('5'):lambda:self.singleWidthLine(),
            ord('6'):lambda:self.doubleWidthLine(),
            ord('8'):lambda:self.screenAlignmentDisplay(),
        }

        self.resetToInitialState()
  
        self.setCursorToHome()

        self.timer.init(period=250, mode=Timer.PERIODIC, callback=self.dispCursor)


    def sc_updateChar(self,x,y):
        idx = self.SC_W*y+x
        c = self.screen[idx]
        a = self.attrib[idx]
        l = self.colors[idx]

        if bit_is_set(a,Blink):
            fore = (l&0x0F)|(1<<3)
            back = (l>>4)|(1<<3)  
        else: 
            fore = l&0x0F 
            back = l>>4   
        if bit_is_set(a,Reverse):
            fore,back = back,fore
        if bit_is_set(self.mode_ex,EX_ScreenReverse):
            fore,back = back,fore
        xx = x*self.CH_W
        yy = y*self.CH_H
        self.fb.fill_rect(xx, yy, self.CH_W, self.CH_H, back)
        self.fb.text(chr(c), xx, yy, fore)
        if bit_is_set(a,Bold):
            self.fb.text(chr(c), xx+1, yy, fore)
        if bit_is_set(a,Underline):
            self.fb.hline(xx, yy+self.CH_H-1, self.CH_W, fore)
    
    def drawCursor(self,x,y):
        xx = x*self.CH_W
        yy = y*self.CH_H
        self.fb.fill_rect(xx, yy, self.CH_W, self.CH_H, clWhite)

    def dispCursor(self,t):
        if self.escMode != NONE:
            return
        self.sc_updateChar(self.p_XP,self.p_YP)
        #self.drawCursor(self.p_XP, self.p_YP)#recover last time replace char
        self.isShowCursor = not self.isShowCursor #flip
        if self.isShowCursor and self.canShowCursor:
            self.drawCursor(self.XP, self.YP)
        else:
            self.sc_updateChar(self.XP,self.YP)
        self.p_XP =self.XP
        self.p_YP = self.YP
        
        
    def sc_updateLine(self,ln):
        for i in range(self.SC_W):
            self.sc_updateChar(i,ln)

    def setCursorToHome(self):
        self.XP=0
        self.YP=0

    def initCursorAndAttribute(self):
        self.cAttr = defaultAttr
        self.cColor = defaultColor
        self.tabs[0:self.SC_W] = b'\x00' * self.SC_W
        for i in range(0, self.SC_W, 8):
            self.tabs[i]=1
        self.setTopAndBottomMargins(1,self.SC_H)
        self.mode = defaultMode
        self.mode_ex = defaultModeEx


    def scroll(self):
        if  bit_is_set(self.mode,CrLf):
            self.XP= 0
        
        self.YP +=1
        if self.YP>self.M_BOTTOM:
            self.YP=self.M_BOTTOM
            n=self.SCSIZE -self.SC_W-((self.MAX_SC_Y+self.M_TOP-self.M_BOTTOM)*self.SC_W)
            idx = self.SC_W*self.M_BOTTOM
            idx3 = self.M_TOP*self.SC_W
            self.screen[idx3:idx3+n]=self.screen[idx3+self.SC_W:idx3+self.SC_W+n]
            self.attrib[idx3:idx3+n]=self.attrib[idx3+self.SC_W:idx3+self.SC_W+n]
            self.colors[idx3:idx3+n]=self.colors[idx3+self.SC_W:idx3+self.SC_W+n]
            
            self.screen[idx : idx + self.SC_W] = b'\x00' * self.SC_W
            self.attrib[idx : idx + self.SC_W] = bytes([defaultAttr] * self.SC_W)
            self.colors[idx : idx + self.SC_W] = bytes([defaultColor] * self.SC_W)
            self.fb.scroll(0, -self.CH_H)
            
            #buf = self.fb.buf
            #width = self.fb.width
            #target = (self.M_TOP*width*self.CH_H)>>1
            #source = ((self.M_TOP + 1) * width * self.CH_H) >> 1
            #n=((self.M_BOTTOM-self.M_TOP)*width*self.CH_H)>>1
            #buf[target:target+n] = buf[source:source+n]
            self.sc_updateLine(self.M_BOTTOM)
            
            #for y in range(self.M_TOP,self.M_BOTTOM+1):
            #    self.sc_updateLine(y)
            
            

    def clearParams(self,m):
        self.escMode = m
        self.isDECPrivateMode = False
        self.nVals = 0
        self.vals[0:4]=array.array('h', [0] * 4)
        self.hasParam=False    
    
    def printChar(self,c):
        if c ==0x1b:
            self.escMode=ES #start of controlling commonds
            return
        if self.escMode==ES:
            if c ==ord('['):
                self.clearParams(CSI)
            elif c ==ord('#'):
                self.clearParams(LSC)
            elif c ==ord('('):
                self.clearParams(G0S)
            elif c ==ord(')'):
                self.clearParams(G1S)
            else:
                self.escSwitch.get(c,lambda:self.unknownSequence(self.escMode, c))()
                self.clearParams(NONE)
            return
        v1=0
        v2=0
        if self.escMode ==CSI:
            self.escMode = CSI2
            self.isDECPrivateMode=(c == ord('?'))
            if self.isDECPrivateMode:
                return
        
        if self.escMode ==CSI2:
            if 48 <= c and c <= 57:
                self.vals[self.nVals]=self.vals[self.nVals]*10 +(c-ord('0'))
                self.hasParam = True
            elif c ==ord(';'):
                self.nVals +=1
                self.hasParam = False
            else:
                if self.hasParam:
                    self.nVals +=1
                if c == ord('A'):
                    v1 = 1 if self.nVals == 0 else self.vals[0]
                    self.reverseIndex(v1)
                elif c == ord('B'):
                    v1 = 1 if self.nVals == 0 else self.vals[0] 
                    self.cursorDown(v1)
                elif c == ord('C'):
                    v1 = 1 if self.nVals == 0 else self.vals[0] 
                    self.cursorForward(v1)
                elif c == ord('D'):
                    v1 = 1 if self.nVals == 0 else self.vals[0] 
                    self.cursorBackward(v1)
                elif c == ord('H') or c==ord('f'):
                    v1=1 if self.nVals == 0 else self.vals[0]
                    v2=1 if self.nVals <= 1 else self.vals[1]
                    self.cursorPosition(v1,v2)
                elif c ==ord('J'):
                    v1=0 if self.nVals == 0 else self.vals[0]
                    self.eraseInDisplay(v1)
                elif c ==ord('K'):
                    v1=0 if self.nVals == 0 else self.vals[0]
                    self.eraseInLine(v1)
                elif c ==ord('L'):
                    v1=1 if self.nVals == 0 else self.vals[0]
                    self.insertLine(v1)
                elif c ==ord('M'):
                    v1=1 if self.nVals == 0 else self.vals[0]
                    self.deleteLine(v1)
                elif c ==ord('c'):
                    v1=0 if self.nVals == 0 else self.vals[0]
                    self.deviceAttributes(v1)
                elif c ==ord('g'):
                    v1=0 if self.nVals == 0 else self.vals[0]
                    self.tabulationClear(v1)
                elif c ==ord('h'):
                    if self.isDECPrivateMode:
                        self.decSetMode(self.vals,self.nVals)
                    else:
                        self.setMode(self.vals,self.nVals)

                elif c ==ord('l'):
                    if self.isDECPrivateMode:
                        self.decResetMode(self.vals,self.nVals)
                    else:
                        self.resetMode(self.vals,self.nVals)

                elif c ==ord('m'):
                    if self.nVals == 0:
                        self.nVals = 1
                    self.selectGraphicRendition(self.vals,self.nVals)
                elif c ==ord('n'):
                    v1=0 if self.nVals == 0 else self.vals[0]
                    self.deviceStatusReport(v1)
                elif c ==ord('q'):
                    v1=0 if self.nVals == 0 else self.vals[0]
                    self.loadLEDs(v1)
                elif c ==ord('r'):
                    v1=1 if self.nVals == 0 else self.vals[0]
                    v2=self.SC_H if self.nVals <= 1 else self.vals[1]
                    self.setTopAndBottomMargins(v1, v2)

                elif c ==ord('y'):
                    if (self.nVals >1 ) and (self.vals[0]==2):
                        self.invokeConfidenceTests(self.vals[1])
                else:
                    self.unknownSequence(self.escMode, c)
                self.clearParams(NONE)
            return

        if self.escMode == LSC:
            self.LSCSwitch(c,lambda:self.unknownSequence(self.escMode, c))()
            self.clearParams(NONE)
            return
        
        if self.escMode == G0S:
            self.setG0charset(c)
            self.clearParams(NONE)
            return
        if self.escMode == G1S:
            self.setG1charset(c)
            self.clearParams(NONE)
            return
        
        if ((c == 0x0a) or (c == 0x0b) or (c == 0x0c)):
            self.scroll()
            return
        
        elif (c == 0x0d):
            self.XP= 0
            return
        
        elif ((c == 0x08) or (c == 0x7f)):
            self.cursorBackward(1)
            idx = self.YP * self.SC_W + self.XP
            self.screen[idx] = 0
            self.attrib[idx] = 0
            self.colors[idx] = self.cColor
            self.sc_updateChar(self.XP, self.YP)
            return
        
        elif c== 0x09:
            idx = -1
            for i in range(self.XP + 1, self.SC_W):
                if self.tabs[i] != 0 :
                    idx = i
                    break
            self.XP =self.MAX_SC_X if (idx == -1) else idx
            return
        if (self.XP<self.SC_W):
            idx = self.YP * self.SC_W + self.XP
            self.screen[idx] = c
            self.attrib[idx] = self.cAttr
            self.colors[idx] = self.cColor
            self.sc_updateChar(self.XP, self.YP)

        self.XP +=1
        if self.XP>=self.SC_W:
            if bit_is_set(self.mode_ex,EX_WrapLine):
                self.scroll()
            else:
                self.XP= self.MAX_SC_X

    def saveCursor(self):
        self.b_XP = self.XP
        self.b_YP = self.YP
        self.bAttr = self.cAttr
        self.bColor = self.cColor
    
    def restoreCursor(self):
        self.XP = self.b_XP
        self.YP = self.b_YP
        self.cAttr = self.bAttr
        self.cColor = self.bColor

    def keypadApplicationMode(self):
        pass

    def keypadNumericMode(self):
        pass

    def index(self,v):
        self.cursorDown(v)

    def nextLine(self):
        self.scroll()

    def horizontalTabulationSet(self):
        self.tabs[self.XP] = 1

    def reverseIndex(self,v):
        self.cursorUp(v)

    def identify(self):
        self.deviceAttributes(0)

    def resetToInitialState(self):
        color = defaultColor>>4
        self.fb.fill(color)
        self.initCursorAndAttribute()
        self.eraseInDisplay(2)

    def cursorUp(self,v):
        self.sc_updateChar(self.XP, self.YP) 
        self.YP -=v
        if self.YP <=self.M_TOP:
            self.YP = self.M_TOP

    def cursorDown(self,v):
        self.sc_updateChar(self.XP, self.YP) 
        self.YP +=v
        if self.YP >=self.M_BOTTOM:
            self.YP=self.M_BOTTOM
    
    def cursorForward(self,v):
        self.sc_updateChar(self.XP, self.YP) 
        self.XP +=v
        if self.XP >=self.SC_W:
            self.XP = self.MAX_SC_X
    
    def cursorBackward(self,v):
        self.sc_updateChar(self.XP, self.YP) 
        self.XP -=v
        if self.XP <=0:
            self.XP = 0

    def cursorPosition(self,y,x):
        self.YP = y - 1
        if self.YP >= self.SC_H:
            self.YP = self.MAX_SC_Y
        self.XP = x - 1
        if self.XP>=self.SC_W:
            self.XP = self.MAX_SC_X
    
    def refreshScreen(self):
        for i in range(self.SC_H):
            self.sc_updateLine(i)
    
    def eraseInDisplay(self,m):
        sl = 0 
        el = 0
        idx = 0
        n = 0
        if m == 0:
            sl = self.YP
            el = self.MAX_SC_Y
            idx = self.YP*self.SC_W+self.XP
            n = self.SCSIZE = (self.YP*self.SC_W +self.XP)
        elif m == 1:
            sl = 0 
            el = self.YP
            idx = 0
            n = self.YP*self.SC_W +self.XP+1
        elif m ==2:
            sl = 0
            el = self.MAX_SC_Y
            idx = 0
            n = self.SCSIZE
        
        if m<=2:
            self.screen[idx : idx + n] = b'\x00' * n
            self.attrib[idx : idx + n] = bytes([defaultAttr])*n
            self.colors[idx : idx + n] = bytes([defaultColor])*n
            for i in range(sl, el + 1):
                self.sc_updateLine(i)

    def eraseInLine(self,m):
        slp = 0
        elp = 0
        if m == 0:
            slp = self.YP*self.SC_W+self.XP
            elp=self.YP*self.SC_W +self.MAX_SC_X
        elif m == 1:
            slp=self.YP*self.SC_W
            elp = self.YP*self.SC_W +self.XP
        elif m == 2:
            slp = self.YP*self.SC_W
            elp = self.YP*self.SC_W+self.MAX_SC_X
        
        if m <=2:
            n = elp-slp +1
            self.screen[slp : slp + n] = b'\x00' * n
            self.attrib[slp : slp + n] = bytes([defaultAttr])*n
            self.colors[slp : slp + n] = bytes([self.cColor])*n
            
            self.sc_updateLine(self.YP)

    def insertLine(self,v):
        rows = v
        if rows == 0:
            return
        if rows >(self.M_BOTTOM+1-self.YP):
            rows = self.M_BOTTOM+1-self.YP
        idx = self.SC_W*self.YP
        n = self.SC_W*rows
        idx2 =idx+n
        move_rows = self.M_BOTTOM+1 -self.YP-rows
        n2 = self.SC_W*move_rows

        if move_rows > 0:
            temp = self.screen[idx : idx + n2]         
            self.screen[idx2 : idx2 + n2] = temp 
            temp = self.attrib[idx : idx + n2]         
            self.attrib[idx2 : idx2 + n2] = temp
            temp = self.colors[idx : idx + n2]         
            self.colors[idx2 : idx2 + n2] = temp      
        self.screen[idx:idx+n]=b'\x00' * n
        self.attrib[idx:idx+n]=bytes([defaultAttr]*n)
        self.colors[idx:idx+n] = bytes([defaultColor]*n)
        for i in range(self.YP,self.M_BOTTOM+1):
            self.sc_updateLine(i)

    def deleteLine(self,v):
        rows = v
        if rows == 0:
            return
        if rows >(self.M_BOTTOM+1-self.YP):
            rows = self.M_BOTTOM+1-self.YP
        idx = self.SC_W*self.YP
        n = self.SC_W*rows
        idx2 =idx+n
        move_rows = self.M_BOTTOM+1 -self.YP-rows
        n2 = self.SC_W*move_rows
        idx3 = (self.M_BOTTOM+1)*self.SC_W - n

        if move_rows > 0:
            temp = self.screen[idx2 : idx2 + n2]         
            self.screen[idx : idx + n2] = temp 
            temp = self.attrib[idx2 : idx2 + n2]         
            self.attrib[idx : idx + n2] = temp
            temp = self.colors[idx2 : idx2 + n2]         
            self.colors[idx : idx + n2] = temp  
        self.screen[idx3:idx3+n]=b'\x00' * n
        self.attrib[idx3:idx3+n]=bytes([defaultAttr]*n)
        self.colors[idx3:idx3+n] = bytes([defaultColor]*n)

        for i in range(self.YP,self.M_BOTTOM+1):
            self.sc_updateLine(i)

    def cursorPositionReport(self,y,x):
        cpr_string = f"\x1b[{y};{x}R"
        self.outputBuff.extend(cpr_string)

    def deviceAttributes(self,m):
        self.outputBuff.extend(b"\x1b[?1;0c")

    def tabulationClear(self,m):
        if m == 0:
            self.tabs[self.XP]=0
        elif m == 3:
            self.tabs[:self.SC_W] = b'\x00' * self.SC_W

    def lineMode(self,m):
        bit_set(self.mode,CrLf,m)
     
    def screenMode(self,m):
        bit_set(self.mode_ex,EX_ScreenReverse,m)
        self.refreshScreen()

    def autoWrapMode(self,m):
        bit_set(self.mode_ex,EX_WrapLine,m)

    def setMode(self,vals,nVals):
        for i in range(nVals):
            if vals[i]==20:
                self.lineMode(True)
            
    def decSetMode(self,vals,nVals):
        for i in range(nVals):
            if vals[i]== 5:
                self.screenMode(True)
            elif vals[i]==7:
                self.autoWrapMode(True)
            elif vals[i]==25:
                self.canShowCursor = True

    def resetMode(self,vals,nVals):
        for i in range(nVals):
            if vals[i]==20:
                self.lineMode(False)

    def decResetMode(self,vals,nVals):
        for i in range(nVals):
            if vals[i]==5:
                self.screenMode(False)
            elif vals[i]==7:
                self.autoWrapMode(False)
            elif vals[i]==25:
                self.canShowCursor = False

    def selectGraphicRendition(self,vals,nVals):
        seq = 0
        r=0
        g=0
        b=0
        cIdx=0
        isFore = True
        for i in range(nVals):
            v=vals[i]
            if seq == 0:
                if v == 0:
                    self.cAttr = 0
                    self.cColor = defaultColor
                elif v == 1:
                    bit_set(self.cAttr,Bold,True)
                elif v == 4:
                    bit_set(self.cAttr,Underline,True)
                elif v == 5:
                    bit_set(self.cAttr,Blink,True)
                elif v == 7:
                    bit_set(self.cAttr,Reverse,True)
                elif v == 21 or v == 22:
                    bit_set(self.cAttr,Bold,False)
                elif v == 24:
                    bit_set(self.cAttr,Underline,False)
                elif v == 25:
                    bit_set(self.cAttr,Blink,False)
                elif v == 27:
                    bit_set(self.cAttr,Reverse,False)
                elif v == 38:
                    seq = 1
                    isFore = True
                elif v == 39:
                    self.cColor &= 0xF0
                    self.cColor |=defaultColor&0x0F
                elif v == 48:
                    seq = 1
                    isFore = False
                elif v == 49:
                    self.cColor &= 0x0F
                    self.cColor |=defaultColor&0xF0
                else:
                    if v>=30 and v<=37:
                        self.cColor &= 0xF0
                        self.cColor |=(v-30)
                    elif v>=40 and v <=47:
                        self.cColor &= 0x0F
                        self.cColor |= (v-40)<<4

            elif seq == 1:
                if v == 2:
                    seq = 3
                elif v == 5:
                    seq = 2
                else:
                    seq = 0
            elif seq == 2:
                if v<256:
                    if v<16:
                        cIdx = v
                    elif v<232:
                        b = ( (v - 16)       % 6) / 3
                        g = (((v - 16) /  6) % 6) / 3
                        r = (((v - 16) / 36) % 6) / 3
                        cIdx = (b << 2) | (g << 1) | r
                    else:
                        if v<244:
                            cIdx = clBlack
                        else:
                            cIdx = clWhite
                    if isFore:
                        self.cColor &= 0xF0
                        self.cColor |=cIdx
                    else:
                        self.cColor &= 0x0F
                        self.cColor |= (cIdx)<<4
                
                seq = 0 

            elif seq == 3:
                seq = 4
            elif seq == 4:
                seq = 5
            elif seq == 5:
                r = 1 if vals[i - 2] >= 128 else 0
                g = 1 if vals[i - 1] >= 128 else 0
                b = 1 if vals[i - 0] >= 128 else 0

                cIdx = (b << 2) | (g << 1) | r
                if isFore:
                    self.cColor &= 0xF0
                    self.cColor |=cIdx
                else:
                    self.cColor &= 0x0F
                    self.cColor |= (cIdx)<<4
                seq = 0    
            else:
                seq = 0

    def deviceStatusReport(self,m):
        if m == 5:
            self.outputBuff.extend(b"\x1b[0n")
        elif m == 6:
            self.cursorPositionReport(self.YP+1, self.XP+1)

    def loadLEDS(self,m):
        pass


    def setTopAndBottomMargins(self,s,e):
        if e <=s:
            return
        self.M_TOP = s -1
        if self.M_TOP > self.MAX_SC_Y:
            self.M_TOP = self.MAX_SC_Y
        self.M_BOTTOM = e -1
        if self.M_BOTTOM>self.MAX_SC_Y:
            self.M_BOTTOM = self.MAX_SC_Y
        self.setCursorToHome()
    
    def invokeConfidenceTests(self,m):
        pass

    def doubleHeightLine_TopHalf(self):
        pass

    def doubleHeightLine_BotomHalf(self):
        pass

    def singleWidthLine(self):
        pass

    def doubleWidthLine(self):
        pass

    def screenAlignmentDisplay(self):
        self.screen[:self.SCSIZE]=b'\x45'*self.SCSIZE
        self.attrib[:self.SCSIZE]=bytes([defaultAttr])*self.SCSIZE
        self.colors[:self.SCSIZE]=bytes([defaultColor])*self.SCSIZE
        for i in range(self.SC_H):
            self.sc_updateLine(i)

    def setG0charset(c):
        pass

    def setG1charset(c):
        pass

    def unknownSequence(self,m, c):
        pass


    def wr(self,input):
        for c in input:
            if ord(c) == 0x07:
                pass
            else:
                self.printChar(ord(c))
        return len(input)

    def rd(self):
        #read from inputIO to get all key input
        self.keyBuf[:] = b'\x00' * len(self.keyBuf)
        n = self.inputIO.readinto(self.keyBuf)
        #append it the self.outputBuff
        if n:
            self.outputBuff.extend(self.keyBuf[0:n])
        #return the first char to the apps
        if self.outputBuff:
            return chr(self.outputBuff.popleft())
        else:
            return None

      
    def readinto(self, buf):
        self.keyBuf[:] = b'\x00' * len(self.keyBuf)
        n=self.inputIO.readinto(self.keyBuf)
        #append it the self.outputBuff
        if n:
            self.outputBuff.extend(self.keyBuf[0:n])
        #return the first char to the apps
        outputNum = min(len(buf),len(self.outputBuff))

        if self.outputBuff:
            pass
        #get the short number between output buf and buf
            for i in range(outputNum):
                buf[i]=self.outputBuff.popleft()
        #output byte
            return outputNum
        #return number
            
        else:
            return None

    def write(self, buf):
        
        return self.wr(buf.decode())

    def rd_raw(self):
        return self.rd()

    def get_screen_size(self):
        return [self.SC_H,self.SC_W]
        

