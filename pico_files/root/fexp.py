from picotui.basewidget import Widget,ChoiceWidget,ACTION_OK
from picotui.defs import *
from picotui.widgets import Dialog,WButton
from picotui.context import Context
from picotui.screen import Screen
from picotui.dialogs import DConfirmation
FEXP_H = '\x1b[33;44m'
FEXP_N = '\x1b[37;44m'



class WFexpStateBar(Widget):
    functionGuid = {
        'default':'',
        '/':FEXP_H+'Enter'+FEXP_N+' Sublevel',
        '..':FEXP_H+'Enter'+FEXP_N+' Uplevel',
        'py':FEXP_H+'F1'+FEXP_N+' RUN '+FEXP_H+'F2'+FEXP_N+' EDIT '+FEXP_H+'F3'+FEXP_N+' COPY '+FEXP_H+'F4'+FEXP_N+' DEL '+FEXP_N,
        'txt':FEXP_H+'F1'+FEXP_N+' EIGENMATH RUN '+FEXP_H+'F2'+FEXP_N+' EDIT '+FEXP_H+'F3'+FEXP_N+' COPY '+FEXP_H+'F4'+FEXP_N+' DEL '+FEXP_N,
        'bmp':FEXP_H+'F1'+FEXP_N+' VIEW '+FEXP_H+'F2'+FEXP_N+' COPY '+FEXP_H+'F3'+FEXP_N+' DEL '+FEXP_N,
    }
    def __init__(self,w=SCREEN_CHR_WIDTH):
        self.t = WFexpStateBar.functionGuid['default']

        self.h = 1
        self.w = w

    def updateGuid(self,extend=""):
        self.t=WFexpStateBar.functionGuid.get(extend,WFexpStateBar.functionGuid.get('default'))
        self.redraw()
    
    def redraw(self):
        self.goto(self.x, self.y)
        self.wr(self.t)


class WPopButtonsGroup(Dialog):
    def __init__(self, x, y, w, h, notice,keyNames):
        super().__init__(x, y, w, h)
        self.notice = notice
        self.keyNum = len(keyNames)
        middlePointSetp = w//(self.keyNum+1)
        x_loc=(w - len(notice))//2
        self.add(x_loc, 1, notice)
        for i in range(len(keyNames)):
            name = keyNames[i]
            width = max(len(name)+2,8)
            b=WButton(width,name)
            b.finish_dialog = i + 1
            x_loc = middlePointSetp*(i+1) - (width//2)
            self.add(x_loc,h-2,b)

    def clear_box(self, left, top, width, height,pattern=" "):
        s = '\xb1'*SCREEN_CHR_WIDTH
        for i in range(SCREEN_CHR_HEIGHT):
            self.goto(0,i)
            self.wr(s)

        super().clear_box(left, top, width, height,pattern)

    def draw_box(self, left, top, width, height):
        super().draw_box(left, top, width, height)
        #draw shadow
        self.goto(left+1,top+height)
        self.wr('\xdb'*width)
        for i in range(height -1):
            self.goto(left+width,top+1+i)
            self.wr('\xdb')

    def result(self):
        return self.loop()


class WFileExplorer(Dialog):
    def __init__(self, x, y, w=53, h=40):
        super().__init__(x, y, w, h, title="File Explorer")
        self.bar =WFexpStateBar(51)
        self.add(1,38,self.bar)

    def handle_key(self, key):
        if key == KEY_ESC:
            #show the question for quit
            res = WPopButtonsGroup(10,17,33,6,"Do you want to quit?",['YES','CANCEL']).result()
            if res == 1:
                return ACTION_OK
            else:
                self.redraw()



def testPop():
    with Context():
        Screen.attr_color(C_WHITE, C_BLUE)
        Screen.cls()
        Screen.attr_reset()
        #a=WPopButtons(10,6,33,6,'Do you want to quit?',['YES','CANCEL'])
        a = WFileExplorer(0,0)
        a.loop()
    
