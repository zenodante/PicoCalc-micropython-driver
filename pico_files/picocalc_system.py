"""
PicoCalc system functions for micropython
Written by: Laika, 4/9/2025

Requires sdcard.py from the official Micropython repository
https://github.com/micropython/micropython-lib/blob/master/micropython/drivers/storage/sdcard/sdcard.py

Features various system functions such as mounting and unmounting the PicoCalc's SD card, a nicer run utility, and an ls utility

"""
import os
import uos
import machine
import sdcard
import gc

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


def run(filename):
    """
    Simple run utility.
    Attempts to run python file provided by filename, returns when done.
    
    Inputs: python file filename/filepath 
    Outputs: None, runs file
    """
    try:
        exec(open(filename).read())
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
    fs_stat = os.statvfs('/')

    # Calculate total and free space
    total_blocks = fs_stat[0]  # Total number of blocks
    free_blocks = fs_stat[3]   # Number of free blocks
    block_size = fs_stat[1]    # Block size in bytes

    # Calculate total and free size in bytes
    total_size = total_blocks * block_size
    free_size = free_blocks * block_size

    # Convert to kilobytes for easier reading
    human_readable_total = human_readable_size(total_size)
    human_readable_free = human_readable_size(free_size)

    # Print the total and free space
    print(f"Total filesystem size: {human_readable_total}")
    print(f"Free filesystem space: {human_readable_free}")
    
def initsd():
    """
    SD Card mounting utility for PicoCalc.
    Utility is specifically for the PicoCalc's internal SD card reader, as it is tuned for its pins.
    
    Inputs: None
    Outputs: None (Mounts SD card if it is present)
    """
    sd = None
    try:
        sd = sdcard.SDCard(
            machine.SPI(0,
                      baudrate=1000000,
                      polarity=0,
                      phase=0,
                      sck=18,
                      mosi=19,
                      miso=16), machine.Pin(17))
        # Mount filesystem
        uos.mount(sd, "/sd")
    except Exception as e:
        print("Failed to mount SD card:", e)
    return sd

def killsd(sd="/sd"):
    """
    SD Card unmounting utility for PicoCalc.
    Could technically function on any device with uos, since it uses the mount point.
    
    Inputs: Filepath to SD mount point
    Output: None, unmounts SD
    """
    try:
        uos.umount(sd)
    except Exception as e: 
        print("Failed to unmount SD card:", e)
    return