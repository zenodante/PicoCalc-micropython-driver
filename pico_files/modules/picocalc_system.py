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
    
def initsd():
    """
    SD Card mounting utility for PicoCalc.
    Utility is specifically for the PicoCalc's internal SD card reader, as it is tuned for its pins.
    
    Inputs: None
    Outputs: None (Mounts SD card if it is present)
    """
    if picocalc.sd is None:
        try:
            picocalc.sd = sdcard.SDCard(
                          machine.SPI(0,
                          baudrate=1000000,
                          polarity=0,
                          phase=0,
                          sck=18,
                          mosi=19,
                          miso=16), machine.Pin(17))
            # Mount filesystem
            uos.mount(picocalc.sd, "/sd")
        except Exception as e:
            print(f"Failed to mount SD card: {e}")
            picocalc.sd = None
    else:
        print("SD card already mounted.")
    return

def killsd(sd_mnt="/sd"):
    """
    SD Card unmounting utility for PicoCalc.
    Could technically function on any device with uos, since it uses the mount point.
    
    Inputs: Filepath to SD mount point
    Output: None, unmounts SD
    """
    if picocalc.sd is not None:
        try:
            uos.umount(sd_mnt)
            picocalc.sd = None
        except Exception as e: 
            print(f"Failed to unmount SD card: {e}")
    return

def checksd(sd_mnt="/sd"):
    if is_dir(sd_mnt):
        print(f"{Fore.GREEN}SD Mounted Successfully.")
    return