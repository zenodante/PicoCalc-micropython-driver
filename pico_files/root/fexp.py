from picotui.basewidget import Widget,ChoiceWidget
from picotui.defs import *
from picotui.widgets import Dialog

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
    def __init__(self, w=SCREEN_CHR_WIDTH):
        self.t = WFexpStateBar.functionGuid['default']
        self.h = 1
        self.w = w

    def updateGuid(self,extend=""):
        self.t=WFexpStateBar.functionGuid.get(extend,WFexpStateBar.functionGuid.get('default'))
        self.redraw()
    
    def redraw(self):
        self.goto(self.x, self.y)
        self.wr(self.t, self.w)


class WPopButtons(Dialog):
    def __init__(self, x, y, w, h, title,keyNames, sel_key=0):
        self.title = title
        self.keyNum = len(keyNames)
        self.middlePointSetp = (w-2)//self.keyNum
        
        super().__init__(x, y, w, h)




class WFileExplorer(ChoiceWidget):
    def __init__(self):
        pass


    def handle_key(self, key):
        if key == KEY_ESC:
            #show the question for quite
            pass

