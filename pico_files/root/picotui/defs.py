# Colors
from micropython import const
C_BLACK    = 0
C_RED      = 1
C_GREEN    = 2
C_YELLOW   = 3
C_BLUE     = 4
C_MAGENTA  = 5
C_CYAN     = 6
C_WHITE    = 7
ATTR_INTENSITY = 8
C_GRAY     = C_BLACK | ATTR_INTENSITY
C_B_RED      = C_RED | ATTR_INTENSITY
C_B_GREEN    = C_GREEN | ATTR_INTENSITY
C_B_YELLOW   = C_YELLOW | ATTR_INTENSITY
C_B_BLUE     = C_BLUE | ATTR_INTENSITY
C_B_MAGENTA  = C_MAGENTA | ATTR_INTENSITY
C_B_CYAN     = C_CYAN | ATTR_INTENSITY
C_B_WHITE    = C_WHITE | ATTR_INTENSITY

def C_PAIR(fg, bg):
    return (bg << 4) + fg


SCREEN_CHR_WIDTH = const(53)
SCREEN_CHR_HEIGHT= const(40)

# Keys


KEY_UP = const(1)
KEY_DOWN = const(2)
KEY_LEFT = const(3)
KEY_RIGHT = const(4)
KEY_HOME = const(5)
KEY_END = const(6)
KEY_PGUP = const(7)
KEY_PGDN = const(8)
KEY_QUIT = const(9)
KEY_ENTER = const(10)
KEY_BACKSPACE = const(11)
KEY_DELETE = const(12)
KEY_TAB = b"\t"
KEY_SHIFT_TAB = const(13)  # 
KEY_ESC = const(20)
KEY_F1 = const(30)
KEY_F2 = const(31)
KEY_F3 = const(32)
KEY_F4 = const(33)
KEY_F5 = const(34)  # 
KEY_F6 = const(35)  # 
KEY_F7 = const(36)  # 
KEY_F8 = const(37) # 
KEY_F9 = const(38)  # 
KEY_F10 = const(39)  # 



KEYMAP = {
b"\x1b[A": KEY_UP,
b"\x1b[B": KEY_DOWN,
b"\x1b[D": KEY_LEFT,
b"\x1b[C": KEY_RIGHT,
b"\x1b[H": KEY_HOME,
b"\x1b[F": KEY_END,
b"\x1bOH": KEY_HOME,
b"\x1bOF": KEY_END,
b"\x1b[4~": KEY_END,
b"\x1b[5~": KEY_PGUP,
b"\x1b[6~": KEY_PGDN,
b"\x03": KEY_QUIT,
b"\r": KEY_ENTER,
b"\x7f": KEY_BACKSPACE,
b"\x1b[3~": KEY_DELETE,
b"\x1b\x1b": KEY_ESC,
b"\x1bOP": KEY_F1,
b"\x1bOQ": KEY_F2,
b"\x1bOR": KEY_F3,
b"\x1bOS": KEY_F4,
}

# Unicode symbols in UTF-8

# DOWNWARDS ARROW
DOWN_ARROW = "\x19"
# BLACK DOWN-POINTING TRIANGLE
DOWN_TRIANGLE = "\x1f"
