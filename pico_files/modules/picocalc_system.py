"""
PicoCalc system functions for micropython
Written by: Laika, 4/19/2025

Requires sdcard.py from the official Micropython repository
https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py

Features various system functions such as mounting and unmounting the PicoCalc's SD card, a nicer run utility, and an ls utility

"""
import os
import uos
import machine
import sdcard
import gc
from micropython import const
import picocalc
from colorer import Fore, Back, Style, print, autoreset

autoreset(True)


def human_readable_size(size):
    """
    Returns input size in bytes in a human-readable format
    
    Inputs: size in bytes
    Outputs: size in closest human-readable unit
    """
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    # Fallthrough isnt even possible to be needed on the PicoCalc, neither is TB, but its a universal function
    return f"{size:.2f} PB"

def is_dir(path):
    """
    Helper function to shittily replace os.path.exists (not in micropython)
    Absolutely not a good replacement, but decent enough for seeing if the SD is mounted
    
    Inputs: path to check for
    Outputs: boolean if path is found
    """
    # List the root directory to check for the existence of the desired path
    try:
        directories = os.listdir('/')
        return path.lstrip('/') in directories
    except OSError:
        return False

def prepare_for_launch(keep_vars=( "gc", "__name__")):
    for k in list(globals()):
        if k not in keep_vars:
            del globals()[k]
    gc.collect()

#provided by _burr_
def screenshot_bmp(buffer, filename, width=320, height=320, palette=None):
    FILE_HEADER_SIZE = const(14)
    INFO_HEADER_SIZE = const(40)
    PALETTE_SIZE = const(16 * 4)  # 16 colors × 4 bytes (BGRA)

    # Default VT100 16-color palette
    if palette is None:
        lut = picocalc.display.getLUT() #get memoryview of the current LUT
        palette = []
        for i in range(16):
            raw = lut[i]
            raw = ((raw & 0xFF) << 8) | (raw >> 8)

            r = ((raw >> 11) & 0x1F) << 3
            g = ((raw >> 5) & 0x3F) << 2
            b = (raw & 0x1F) << 3
            palette.append((r, g, b))
        '''
        palette = [
            (0x00, 0x00, 0x00),  # 0 black
            (0x80, 0x00, 0x00),  # 1 red
            (0x00, 0x80, 0x00),  # 2 green
            (0x80, 0x80, 0x00),  # 3 yellow
            (0x00, 0x00, 0x80),  # 4 blue
            (0x80, 0x00, 0x80),  # 5 magenta
            (0x00, 0x80, 0x80),  # 6 cyan
            (0xc0, 0xc0, 0xc0),  # 7 white (light gray)
            (0x80, 0x80, 0x80),  # 8 bright black (dark gray)
            (0xff, 0x00, 0x00),  # 9 bright red
            (0x00, 0xff, 0x00),  # 10 bright green
            (0xff, 0xff, 0x00),  # 11 bright yellow
            (0x00, 0x00, 0xff),  # 12 bright blue
            (0xff, 0x00, 0xff),  # 13 bright magenta
            (0x00, 0xff, 0xff),  # 14 bright cyan
            (0xff, 0xff, 0xff),  # 15 bright white
        ]
        '''
    row_bytes = ((width + 1) // 2 + 3) & ~3  # align to 4-byte boundary
    pixel_data_size = row_bytes * height
    file_size = FILE_HEADER_SIZE + INFO_HEADER_SIZE + PALETTE_SIZE + pixel_data_size
    pixel_data_offset = FILE_HEADER_SIZE + INFO_HEADER_SIZE + PALETTE_SIZE

    with open(filename, "wb") as f:
        # BMP file header
        f.write(b'BM')
        f.write(file_size.to_bytes(4, 'little'))
        f.write((0).to_bytes(4, 'little'))  # Reserved
        f.write(pixel_data_offset.to_bytes(4, 'little'))

        # DIB header
        f.write(INFO_HEADER_SIZE.to_bytes(4, 'little'))
        f.write(width.to_bytes(4, 'little'))
        f.write(height.to_bytes(4, 'little'))
        f.write((1).to_bytes(2, 'little'))  # Planes
        f.write((4).to_bytes(2, 'little'))  # Bits per pixel
        f.write((0).to_bytes(4, 'little'))  # No compression
        f.write(pixel_data_size.to_bytes(4, 'little'))
        f.write((0).to_bytes(4, 'little'))  # X pixels per meter
        f.write((0).to_bytes(4, 'little'))  # Y pixels per meter
        f.write((16).to_bytes(4, 'little'))  # Colors in palette
        f.write((0).to_bytes(4, 'little'))  # Important colors

        # Palette (BGRA)
        for r, g, b in palette:
            f.write(bytes([b, g, r, 0]))

        # Pixel data (bottom-up)
        for row in range(height - 1, -1, -1):
            start = row * ((width + 1) // 2)
            row_data = buffer[start:start + ((width + 1) // 2)]
            f.write(row_data)
            f.write(bytes(row_bytes - len(row_data)))  # Padding


def run(filename):
    """
    Simple run utility.
    Attempts to run python file provided by filename, returns when done.
    
    Inputs: python file filename/filepath 
    Outputs: None, runs file
    """
    try:
        exec(open(filename).read(), globals())
    except OSError:
        print(f"Failed to open file: {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")
    return

def files(directory="/"):
    """
    Basic ls port.
    
    Inputs: directory/filepath to list files and directories in
    Outputs: Print of all files and directories contained, along with size
    """
    try:
        # List entries in the specified directory
        entries = uos.listdir(directory)
    except OSError as e:
        print(f"Error accessing directory {directory}: {e}")
        return

    print(f"\nContents of directory: {directory}\n")
    for entry in entries:
        try:
            # Construct the full path
            full_path = directory.rstrip("/") + "/" + entry
            stat = uos.stat(full_path)
            size = stat[6]

            # Check if entry is a directory or a file
            if stat[0] & 0x4000:  # Directory
                print(f"{entry:<25} <DIR>")
            else:  # File
                readable_size = human_readable_size(size)
                print(f"{entry:<25} {readable_size:<9}")
        except OSError as e:
            print(f"Error accessing {entry}: {e}")
    return

def memory():
    gc.collect()
    # Get the available and free RAM
    free_memory = gc.mem_free()
    allocated_memory = gc.mem_alloc()

    # Total memory is the sum of free and allocated memory
    total_memory = free_memory + allocated_memory
    
    human_readable_total = human_readable_size(total_memory)
    human_readable_free = human_readable_size(free_memory)
    
    print(f"Total RAM: {human_readable_total}")
    print(f"Free RAM: {human_readable_free}")

def disk():
    """
    Prints available flash and SD card space (if mounted) as well as totals
    
    Input: None
    Outputs: None, prints disk statuses
    """
    filesystem_paths = ['/', '/sd']
    for path in filesystem_paths:
        if is_dir(path) or path == '/':
            if path == '/sd':
                # Indicate SD card status
                print("SD card mounted.")
                print("Indexing SD Card, Please Wait.")
            try:
                fs_stat = os.statvfs(path)
                block_size = fs_stat[1]
                total_blocks = fs_stat[2]
                free_blocks = fs_stat[3]
                total_size = total_blocks * block_size
                free_size = free_blocks * block_size
                human_readable_total = human_readable_size(total_size)
                human_readable_free = human_readable_size(free_size)

                if path == '/':
                    print(f"Total filesystem size: {human_readable_total}")
                    print(f"Free filesystem space: {human_readable_free}")
                else:
                    print(f"Total SD size: {human_readable_total}")
                    print(f"Free SD space: {human_readable_free}")

            except OSError:
                print(f"Unexpected error accessing filesystem at '{path}'.")

        else:
            if path == '/sd':
                print("No SD Card Mounted.")