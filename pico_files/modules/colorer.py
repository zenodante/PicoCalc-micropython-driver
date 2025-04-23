import sys
import builtins

# kind of a misnomer, is module level
_global_autoreset = False

class Fore:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"  # Often used as "purple"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[39m"

    GREY = "\033[48;5;250m"  # Bright black didnt work but this does
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"  # Often used as bright "purple"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Purple can be aliasing magenta
    PURPLE = MAGENTA
    BRIGHT_PURPLE = BRIGHT_MAGENTA


class Back:
    BLACK = "\033[40m"
    RED = "\033[41m"
    GREEN = "\033[42m"
    YELLOW = "\033[43m"
    BLUE = "\033[44m"
    MAGENTA = "\033[45m"  # Often used as "purple"
    CYAN = "\033[46m"
    WHITE = "\033[47m"
    RESET = "\033[49m"

    GREY = "\033[48;5;250m"  # Bright black didnt work but this does
    BRIGHT_RED = "\033[101m"
    BRIGHT_GREEN = "\033[102m"
    BRIGHT_YELLOW = "\033[103m"
    BRIGHT_BLUE = "\033[104m"
    BRIGHT_MAGENTA = "\033[105m"  # Often used as bright "purple"
    BRIGHT_CYAN = "\033[106m"
    BRIGHT_WHITE = "\033[107m"

    # Purple can be aliasing magenta
    PURPLE = MAGENTA
    BRIGHT_PURPLE = BRIGHT_MAGENTA
    
class Style:
    BRIGHT = "\033[1m"
    DIM = "\033[2m"
    NORMAL = "\033[22m"
    UNDERLINE = "\033[4m"
    FLASHING = "\033[5m"
    RESET_ALL = "\033[0m"
    
def autoreset(state):
    """Set the autoreset state for the library."""
    global _global_autoreset
    _global_autoreset = state
    
def print(*args, sep=' ', end='\n', file=sys.stdout):
    """Custom print function that respects the global autoreset setting."""
    global _global_autoreset
    text = sep.join(map(str, args))
    if _global_autoreset:
        text += Style.RESET_ALL
    builtins.print(text, end=end, file=file)
    
