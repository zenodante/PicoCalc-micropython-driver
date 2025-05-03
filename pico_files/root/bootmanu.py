from picocalc import terminal

SELECTOR = '\x10'  # Code Page 437: ►
MENU_ITEMS = [
    "Boot to REPL on Screen",
    "Boot to USB REPL"
]

def clear_screen(w=53, h=40):
    terminal.wr("\x1b[30;46m")  # fg=black, bg=cyan
    terminal.wr("\x1b[2J")  # Clear screen
    terminal.wr("\x1b[H")   # Move cursor to home
    
    # Fill the screen with colored background
    for row in range(h):
        terminal.wr(f"\x1b[{row+1};1H" + " " * w)

def move_cursor(y, x):
    terminal.wr(f"\x1b[{y};{x}H")

def draw_box(x, y, w, h):
    # Draw the box content (filled area) - cyan background
    terminal.wr("\x1b[30;46m")  # fg=black, bg=cyan
    for i in range(h):
        move_cursor(y + i, x)
        terminal.wr(" " * w)
    
    # Draw the shadow using Code Page 437 character 0xB1 (░)
    terminal.wr("\x1b[90;40m")  # fg=bright black (gray), bg=black for shadow
    
    # Draw right shadow column
    for i in range(h):
        move_cursor(y + i, x + w)
        terminal.wr("\xB1")  # Code Page 437: ░ (light shade)
    
    # Draw bottom shadow row
    move_cursor(y + h, x + 1)
    terminal.wr("\xB1" * w)
    
    # Restore main color
    terminal.wr("\x1b[30;46m")  # Return to fg=black, bg=cyan

def draw_menu(x, y, selected):
    terminal.wr("\x1b[30;46m")  # fg=black, bg=cyan - make sure text has right colors
    for i, text in enumerate(MENU_ITEMS):
        move_cursor(y + i, x)
        marker = SELECTOR if i == selected else " "
        terminal.wr(f"[{marker}] {text}")

def update_selector(x, y, old_idx, new_idx):
    terminal.wr("\x1b[30;46m")  # fg=black, bg=cyan
    move_cursor(y + old_idx, x + 1)  # +1 to position after the opening bracket
    terminal.wr(" ")  # Clear old selector
    move_cursor(y + new_idx, x + 1)  # +1 to position after the opening bracket
    terminal.wr(SELECTOR)  # Draw new selector

def boot_menu():
    screen_w, screen_h = 53, 40
    clear_screen(screen_w, screen_h)
    terminal.wr("\x1b[30;46m")  # fg=black, bg=cyan - set main colors
    terminal.wr("\x1b[?25l")  # Hide cursor
    
    W = 30
    H = len(MENU_ITEMS) + 2
    
    # Center the box
    x = (screen_w // 2) - (W // 2)
    y = (screen_h // 2) - (H // 2)
    
    draw_box(x, y, W, H)
    selected = 0
    draw_menu(x + 2, y + 1, selected)  # Initial draw
    
    while True:
        ch = terminal.rd()
        old_selected = selected
        
        if ch == b'\x1b':  # ESC
            ch2 = terminal.rd()
            if ch2 == b'[':
                ch3 = terminal.rd()
                if ch3 == b'A':  # Up
                    selected = (selected - 1) % len(MENU_ITEMS)
                elif ch3 == b'B':  # Down
                    selected = (selected + 1) % len(MENU_ITEMS)
        elif ch == b'\r':  # Enter
            break
            
        if selected != old_selected:
            update_selector(x + 2, y + 1, old_selected, selected)
    
    terminal.wr("\x1b[?25h")  # Show cursor again
    terminal.wr("\x1b[0m")    # Reset terminal colors
    return selected