from picocalc import display, terminal,keyboard
import time


MAX_ITER = 16

# fixed-point
FIXED_SHIFT = 10  # =*1024
FIXED_ONE = 1 << FIXED_SHIFT




def render_mandelbrot(scale=1024, center_x=0, center_y=0):
    span_x = (3 * FIXED_ONE) * FIXED_ONE // scale
    span_y = (3 * FIXED_ONE) * FIXED_ONE // scale
    max_iter = 16

    for y in range(320):
        cy = center_y - (span_y // 2) + (y * span_y) // 320
        for x in range(320):
            cx = center_x - (span_x // 2) + (x * span_x) // 320
            zx, zy = 0, 0
            for i in range(max_iter):
                zx2 = (zx * zx) >> FIXED_SHIFT
                zy2 = (zy * zy) >> FIXED_SHIFT
                if zx2 + zy2 > (4 << FIXED_SHIFT):
                    break
                zxy = (zx * zy) >> (FIXED_SHIFT - 1)
                zy = zxy + cy
                zx = zx2 - zy2 + cx

            if zx2 + zy2 <= (4 << FIXED_SHIFT):
                color = 0  # 
            else:
                color = (i % 15) + 1  # 

            display.pixel(x, y, color)


terminal.dryBuffer()
#terminal.stopRefresh()
terminal.wr("\x1b[?25l")  # hide cursor
temp =bytearray(1)
for zoom in range(1024, 8192, 16):  # 从1倍放大到8倍
    render_mandelbrot(scale=zoom, center_x=0, center_y=0)
    terminal.wr("\x1b[40;1HPress any key to break...")
    if keyboard.readinto(temp):
        break
    time.sleep(0.1)
#render_mandelbrot(scale=1024, center_x=0, center_y=0)

#terminal.wr("\x1b[40;1HPress any key to continue...")
#terminal.rd()
display.fill(0) #clean the screen
terminal.wr("\x1b[2J\x1b[H")#move the cursor to the top, and clear the terminal buffer
#terminal.recoverRefresh()
terminal.wr("\x1b[?25h")  # show cursor