from picocalc import display, terminal,keyboard
import time
import micropython
display.switchPredefinedLUT('pico8')
MAX_ITER = 16

# fixed-point
FIXED_SHIFT = 10  # =*1024
FIXED_ONE = 1 << FIXED_SHIFT

@micropython.viper
def mandelbrot_pixel(cx: int, cy: int, max_iter: int, fixed_shift: int) -> int:
    zx = 0
    zy = 0
    for i in range(max_iter):
        zx2 = (zx * zx) >> fixed_shift
        zy2 = (zy * zy) >> fixed_shift
        if zx2 + zy2 > (4 << fixed_shift):
            return i
        zxy = (zx * zy) >> (fixed_shift - 1)
        zy = zxy + cy
        zx = zx2 - zy2 + cx
    return max_iter

@micropython.native
def render_mandelbrot(scale=1024, center_x=0, center_y=0):
    span_x = (3 * FIXED_ONE) * FIXED_ONE // scale
    span_y = (3 * FIXED_ONE) * FIXED_ONE // scale
    max_iter = 16

    for y in range(312):
        cy = center_y - (span_y // 2) + (y * span_y) // 320
        for x in range(320):
            cx = center_x - (span_x // 2) + (x * span_x) // 320
            m = mandelbrot_pixel(cx, cy, max_iter, FIXED_SHIFT)
            if m == max_iter:
                color = 0
            else:
                color = (m % 15) + 1
            display.pixel(x, y, color)


terminal.dryBuffer()
#terminal.stopRefresh()
terminal.wr("\x1b[?25l")  # hide cursor
temp =bytearray(1)
for zoom in range(1024, 8192, 64):  # from 1x to 8x zoom
    render_mandelbrot(scale=zoom, center_x=0, center_y=0)
    terminal.wr("\x1b[40;1HPress any key to break...")
    #display.show()  # show in manual refresh mode
    if keyboard.readinto(temp):
        break
    time.sleep(0.1)


#terminal.wr("\x1b[40;1HPress any key to continue...")
#terminal.rd()
del temp,MAX_ITER, FIXED_SHIFT, FIXED_ONE, render_mandelbrot
display.fill(0) #clean the screen
display.restLUT()
terminal.wr("\x1b[2J\x1b[H")#move the cursor to the top, and clear the terminal buffer
#terminal.recoverRefresh()
terminal.wr("\x1b[?25h")  # show cursor