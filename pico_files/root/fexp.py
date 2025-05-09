from picotui.basewidget import Widget,ItemSelWidget,ACTION_OK
from picotui.defs import *
from picotui.widgets import Dialog,WButton,WListBox
from picotui.context import Context
from picotui.screen import Screen
from picotui.dialogs import DConfirmation
from picotui.style import *
import os
FEXP_H = '\x1b[33m'
FEXP_N = '\x1b[30m'



def list_dir_separately(path="."):
    files = []
    dirs = []

    for entry in os.listdir(path):
        full_path = path + "/" + entry if path != "/" else "/" + entry
        mode = os.stat(full_path)[0]
        if mode & 0x4000:  # 0x4000 means it's a directory
            dirs.append(entry)
        else:
            size = os.stat(full_path)[6]
            files.append((entry,size))

    return dirs, files

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
        self.wr(' '*(SCREEN_CHR_WIDTH-2))
        self.goto(self.x, self.y)
        self.wr(self.t)
        #self.clear_to_eol()


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


class WFileList(ItemSelWidget):
    def __init__(self,w,h,path='/'):
        self.path = path
        super().__init__([])
        self.w = w
        self.h = h
        self.refreshList(path)

    
    def redraw(self):
        dispLineNum = self.currentdispBottom - self.currentdispTop + 1
        for i in range(dispLineNum):
            itemIdx = i + self.currentdispTop
            self.goto(self.x,self.y+i)
            self.show_line(self.items[itemIdx],itemIdx)

    def createListItem(self,path):
        folders,files=list_dir_separately(path)
        items = list()
        if path !='.' or path != '/': 
            items.append('..')
        for folder in folders:
            items.append(folder +'/')
        for file in files:
            items.append(file[0])
        return items


    def handle_key(self,key):
        if key == KEY_UP:
            self.move_sel(-1)
        elif key == KEY_DOWN:
            self.move_sel(1)
        elif key == KEY_ENTER:
            if self.items[self.choice]=='..':
                last_slash_index = self.path.rfind('/')
                if last_slash_index == -1:
                    self.path = '/'
                else:
                    self.path = self.path[:last_slash_index]
                self.refreshList(self.path)
                self.redraw()
                self.signal("changed")
            elif self.items[self.choice][-1]=='/':
                self.path = self.path + "/" + self.items[self.choice][:-1] if self.path != "/" else "/" + self.items[self.choice][:-1]
                self.refreshList(self.path)
                self.redraw()
                self.signal("changed")
    
    def refreshList(self,path):
        self.items=self.createListItem(path)
        self.choice  = 0
        self.totalLineNum = len(self.items)
        self.currentdispTop = 0
        self.currentdispBottom = min(self.totalLineNum,self.h)-1


    def move_sel(self,direction):
        oldChoice = self.choice
        if self.choice + direction <0:
            self.choice = 0
        elif self.choice + direction > self.totalLineNum -1:
            self.choice = self.totalLineNum -1
        else:
            self.choice = (self.choice + direction)
        if self.choice < self.currentdispTop:
            self.currentdispTop -=1
            self.currentdispBottom = min(self.currentdispTop + self.h,self.totalLineNum)-1
        elif self.choice< self.currentdispBottom:
            self.currentdispTop +=1
            self.currentdispBottom +=1    
        if self.choice != oldChoice:
            self.redraw()
            self.signal("changed")

    def show_line(self, l, i):
        hlite = self.choice == i
        if hlite:
            if self.focus:
                self.attr_color(picotui_style[LISTBOX_FOCUS_FRONT_COLOR], picotui_style[LISTBOX_FOCUS_BG_COLOR])
            else:
                self.attr_color(picotui_style[LISTBOX_NO_FOCUS_FRONT_COLOR], picotui_style[LISTBOX_NO_FOCUS_BG_COLOR])
        if i != -1:
            self.wr(l)
        self.clear_num_pos(self.w - len(l))
        if hlite:
            self.attr_reset()


class FileExplorer(Dialog):
    def __init__(self, x, y,path='/', w=53, h=40):
        super().__init__(x, y, w, h, title="File Explorer")
        self.bar =WFexpStateBar(51)
        #self.currentRoot = '.'
        #dirs,files = list_dir_separately(self.currentRoot)
        #self.filenamelist = []
        #for dir in dirs:
        #    self.filenamelist.append(dir+'/')
        #for file in files:
        #    self.filenamelist.append(file[0])
        #self.filelistBox = WListBox(51, 34, self.filenamelist)
        self.filelistBox = WFileList(51,37,path)
        self.add(1, 1, self.filelistBox)
        self.filelistBox.on("changed",self.updatebar)
        self.add(1,38,self.bar)


    def handle_key(self, key):
        res = super().handle_key(key)
        if key == KEY_ESC:
            #show the question for quit
            res = WPopButtonsGroup(10,17,33,6,"Do you want to quit?",['YES','CANCEL']).result()
            if res == 1:
                return ACTION_OK
            else:
                self.redraw()
        else:
            return res
    
    def updatebar(self,trigerWidget):
        #choice = self.filelistBox.choice
        choice = trigerWidget.choice
        filename  = self.filenamelist[choice]
        if filename == '..':
            self.bar.updateGuid(filename)
        else:
            self.bar.updateGuid(filename.split('.')[-1])

        

def testPop():
    with Context():
        Screen.attr_color(C_WHITE, C_BLUE)
        Screen.cls()
        Screen.attr_reset()
        #a=WPopButtons(10,6,33,6,'Do you want to quit?',['YES','CANCEL'])
        a = FileExplorer(0,0)
        a.loop()
    
