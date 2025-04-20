"""
Limited Colorama Port to Micropython
Written by: Laika, 4/19/2025

Allows for coloring using Fore, Back, and Style like Colorama
Autoreset functionality is also supplied by shadowing print
"""
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
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[39m"
    
class Back:
    BLACK = "\033[40m"
    RED = "\033[41m"
    GREEN = "\033[42m"
    YELLOW = "\033[43m"
    BLUE = "\033[44m"
    MAGENTA = "\033[45m"
    CYAN = "\033[46m"
    WHITE = "\033[47m"
    RESET = "\033[49m"
    
class Style:
    BRIGHT = "\033[1m"
    DIM = "\033[2m"
    NORMAL = "\033[22m"
    UNDERLINE = "\033[4m"
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
    
