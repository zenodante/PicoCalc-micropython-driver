from picocalc import PicoDisplay, PicoKeyboard
from fbconsole import FBConsole
import os
pd = PicoDisplay(320,320)
kb = PicoKeyboard()
fb=FBConsole( pd, bgcolor=0, fgcolor=2, width=320, height=320,readobj=kb,fontX=6,fontY=8)
os.dupterm(fb) 
