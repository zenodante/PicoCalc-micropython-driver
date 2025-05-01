import math
from picocalc import display,terminal

# ------------------------------------------------------------------
# VT100 palette index (4 bit, format: BRIGHT R G B)
#   bit3 = BRIGHT (1 = bright version), bit2 = Red, bit1 = Green, bit0 = Blue
# 0: Black      1: Red         2: Green       3: Yellow
# 4: Blue       5: Magenta     6: Cyan        7: White
# 8: Bright Black(Gray)  9: Bright Red  10: Bright Green  11: Bright Yellow
# 12: Bright Blue       13: Bright Magenta  14: Bright Cyan  15: Bright White
# ------------------------------------------------------------------

def rgb(r, g, b):

    bright = 1 if max(r, g, b) > 127 else 0
    red    = 1 if r > 127 else 0
    green  = 1 if g > 127 else 0
    blue   = 1 if b > 127 else 0
    return (bright << 3) | (red << 2) | (green << 1) | blue

def rotation(width, height, fun, fb):

    w2 = width  // 2
    h2 = height // 2

    fb.fill(0) 

    m = n = 0

    for x in range(w2):
        p = int(math.sqrt(w2*w2 - x*x))
        for v in range(2 * p):
            z     = v - p
            r_val = math.sqrt(x*x + z*z) / w2   
            q     = fun(r_val)
            y     = round(z/3 + q * h2)         

            c = rgb(int(r_val*255), int((1-r_val)*255), 128)

            if v == 0:
                m = n = y
                draw = True
            elif y > m:
                m = y
                draw = True
            elif y < n:
                n = y
                draw = True
            else:
                draw = False

            if draw:
                # 对称画两点
                fb.pixel(w2 - x, h2 - y, c)
                fb.pixel(w2 + x, h2 - y, c)


WIDTH, HEIGHT = 320,312



def my_fun(r):
    return (r - 1) * math.sin(r * 24)
    #return 2.5 * (1 - r) * (1 - r) + 2 * r * r * 0.7 - 1.5
    #return (math.sin(r * 2 * math.pi) + 1) / 2


terminal.dryBuffer()
#terminal.stopRefresh()
terminal.wr("\x1b[?25l")  # hide cursor
# Execute rotation drawing
rotation(WIDTH, HEIGHT, my_fun, display)

terminal.wr("\x1b[40;1HPress any key to continue...")
terminal.rd()
display.fill(0) #clean the screen
terminal.wr("\x1b[2J\x1b[H")#move the cursor to the top, and clear the terminal buffer

del WIDTH
del HEIGHT



#terminal.recoverRefresh()
terminal.wr("\x1b[?25h")  # show cursor

