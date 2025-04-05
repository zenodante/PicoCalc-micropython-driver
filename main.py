from picocalc import PicoDisplay, PicoKeyboard
from fbconsole import FBConsole
pd = PicoDisplay(320,320)
kb = PicoKeyboard()
FBConsole( pd, bgcolor=0, fgcolor=2, width=320, height=320,readobj=kb,fontX=6,fontY=8)
