from picocalc import display,keyboard,terminal


terminal.dryBuffer()


terminal.wr("\x1b[?25l")  # hide cursor
terminal.stopRefresh()
i=0
temp =bytearray(1)

def processKey():
    # Read a key from the keyboard
    if keyboard.readinto(temp):
        key = temp[0]
        if key == ord('E') or key == ord('e'):
            return True
    return False    

while(True):
    while not display.isScreenUpdateDone():
        pass
    if processKey():
        break
    display.fill(i)
    i+=1
    if i>15:
        i=0
    terminal.wr("\x1b[40;1HPress \'E\' to break...")
    display.show() 


terminal.recoverRefresh()
display.fill(0) #clean the screen
display.restLUT()
terminal.wr("\x1b[2J\x1b[H")#move the cursor to the top, and clear the terminal buffer

terminal.wr("\x1b[?25h")  # show cursor