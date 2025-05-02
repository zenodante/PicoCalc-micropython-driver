from picocalc import display,keyboard,terminal
import math
import micropython
import gc
from array import array
import time
# Enable full optimizations
micropython.opt_level(3)

# Initialize a 320×320, 4-bit grayscale framebuffer
WIDTH, HEIGHT = 320, 312


# Precompute constants
GRID = 15
GRID_POINTS = GRID * GRID
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
FOCAL_LEN = 100
MAX_COLOR = 15

# Viewport boundaries for culling
VIEWPORT_MIN_X = -20
VIEWPORT_MAX_X = WIDTH + 20
VIEWPORT_MIN_Y = -20
VIEWPORT_MAX_Y = HEIGHT + 20

# --- PRE-ALLOCATE ALL MEMORY STRUCTURES ---

# Pre-allocate coords array
coords = array('f', [0.0] * GRID)
for i in range(GRID):
    coords[i] = ((i / (GRID-1)) * 2 - 1) * 1.2

# Pre-allocate grid points - store as flat arrays for better memory efficiency
grid_x = array('f', [0.0] * GRID_POINTS)
grid_y = array('f', [0.0] * GRID_POINTS)
grid_r = array('f', [0.0] * GRID_POINTS)

# Fill the grid arrays
idx = 0
for gy in coords:
    for gx in coords:
        grid_x[idx] = gx
        grid_y[idx] = gy
        grid_r[idx] = math.sqrt(gx*gx + gy*gy)
        idx += 1



# Pre-allocate arrays for projected coordinates
proj_x = array('i', [0] * GRID_POINTS)
proj_y = array('i', [0] * GRID_POINTS)
proj_size = array('i', [0] * GRID_POINTS)
proj_depth = array('f', [0.0] * GRID_POINTS)
proj_color = array('i', [0] * GRID_POINTS)
proj_visible = array('b', [0] * GRID_POINTS)  # 0 = invisible, 1 = visible

# Pre-allocate draw order array (indices into the projection arrays)
draw_order = array('i', list(range(GRID_POINTS)))

# Pre-allocate sine lookup table for faster sine calculations
SIN_LUT_SIZE = 256
sin_lut = array('f', [0.0] * SIN_LUT_SIZE)
for i in range(SIN_LUT_SIZE):
    sin_lut[i] = math.sin(i * 2 * math.pi / SIN_LUT_SIZE)

# Pre-allocate the sorting key array
# This will hold depth values for the stable sorting algorithm
sort_keys = array('f', [0.0] * GRID_POINTS)

@micropython.native
def fast_sin(angle: float) -> float:
    # Fast sine approximation using lookup table
    index = int((angle % (2 * math.pi)) * SIN_LUT_SIZE / (2 * math.pi))
    return sin_lut[index & (SIN_LUT_SIZE - 1)]

# Simplified bubble sort for depth sorting - avoid creating new data structures
@micropython.native
def depth_sort(visible_count):
    # Copy depths to sort_keys array for items that are visible
    for i in range(visible_count):
        idx = draw_order[i]
        sort_keys[i] = proj_depth[idx]
    
    # Simple bubble sort - works well for mostly-sorted data as in 3D scenes
    for i in range(visible_count):
        for j in range(visible_count - i - 1):
            if sort_keys[j] < sort_keys[j + 1]:
                # Swap the sort keys
                sort_keys[j], sort_keys[j + 1] = sort_keys[j + 1], sort_keys[j]
                # Swap the indices in draw_order
                draw_order[j], draw_order[j + 1] = draw_order[j + 1], draw_order[j]

# Combined rotation and perspective projection with viewport culling
@micropython.native
def transform_points(amplitude: float, freq: float, phase: float, 
                     cam_dist: float, cx: float, sx: float, cy: float, sy: float):
    # Reset visibility count
    visible_count = 0
    
    # Process all grid points
    for i in range(int(GRID_POINTS)):
        # Get original coordinates
        x0 = grid_x[i]
        y0 = grid_y[i]
        r = grid_r[i]
        
        # Compute height
        z0 = amplitude * fast_sin(r * 2 * math.pi * freq + phase)
        
        # Apply rotations - implemented inline to avoid function calls
        # First rotate around Y (horizontal rotation around center)
        x1 = z0 * sy + x0 * cy
        z1 = z0 * cy - x0 * sy
        
        # Then rotate around X (vertical tilt/pitch)
        y2 = y0 * cx - z1 * sx
        z2 = y0 * sx + z1 * cx
        
        # Store rotated point
        #point_x[i] = x1
        #point_y[i] = y2
        #point_z[i] = z2
        
        # Apply perspective projection
        z_adj = z2 + cam_dist
        if z_adj <= 0.001:
            z_adj = 0.001
        
        inv_z = FOCAL_LEN / z_adj
        px = int(x1 * inv_z) + HALF_WIDTH
        py = int(y2 * inv_z) + HALF_HEIGHT
        
        # Check if point is within viewport
        if (px < VIEWPORT_MIN_X or px > VIEWPORT_MAX_X or 
            py < VIEWPORT_MIN_Y or py > VIEWPORT_MAX_Y):
            proj_visible[i] = 0  # Not visible
            continue
        
        # Store projected coordinates
        proj_x[i] = px
        proj_y[i] = py
        proj_size[i] = max(1, int(inv_z * 4))
        proj_depth[i] = z_adj
        
        # Calculate color based on height (z2 is the rotated z value)
        color = int(((z2 / amplitude) + 1) * 0.5 * MAX_COLOR)
        proj_color[i] = max(0, min(MAX_COLOR, color))
        
        # Mark as visible and add to draw order
        proj_visible[i] = 1
        draw_order[visible_count] = i
        visible_count += 1
    
    return visible_count

# Main drawing function - completely rewritten to avoid memory allocations
@micropython.native
def draw_wave(amplitude, freq, phase, cam_dist, pitch, yaw):
    # Clear framebuffer
    
    
    # Precompute rotation values
    cx, sx = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)

    
    # Transform all points - apply rotation, projection, and viewport culling
    visible_count = transform_points(amplitude, freq, phase, cam_dist, cx, sx, cy, sy)
    
    # Skip sorting and drawing if no points are visible
    if visible_count == 0:
        return
    
    # Sort points by depth
    depth_sort(visible_count)
    while not display.isScreenUpdateDone():
        pass # Wait for previous screen update to finish
    # Draw points in back-to-front order
    display.fill(0)
    terminal.wr("\x1b[39;1Hvisible"+str(visible_count))
    for i in range(visible_count):
        # Get index from draw order
        idx = draw_order[i]
        
        # Skip if not visible (should not happen due to how visible_count works, but just in case)
        if not proj_visible[idx]:
            continue
        
        # Draw the point as a filled rectangle
        x = proj_x[idx]
        y = proj_y[idx]
        size = proj_size[idx]
        color = proj_color[idx]
        
        half_size = size // 2
        display.fill_rect(x - half_size, y - half_size, size, size, color)

def processKey():
    # Read a key from the keyboard
    if keyboard.readinto(temp):
        key = temp[0]
        if key == ord('E') or key == ord('e'):
            return True
    return False    

terminal.dryBuffer()


terminal.wr("\x1b[?25l")  # hide cursor
terminal.stopRefresh()

gamma = 2.2
# Predefine an array of 16 zeros (type 'H')
color_lut = array('H', [0] * 16)
for i in range(16):
    # normalized position [0..1]
    f = i / 15
    # gamma-corrected channel value [0..31]
    v = int(31 * (f ** (1 / gamma)) + 0.5)
    # red & blue channels for purple, green remains 0
    r5 = v
    g6 = 0
    b5 = v
    # pack into RGB565 format
    rgb565 = (r5 << 11) | (g6 << 5) | b5
    # swap bytes (low byte first)
    swapped = ((rgb565 & 0xFF) << 8) | (rgb565 >> 8)
    color_lut[i] = swapped

display.setLUT(color_lut)
temp =bytearray(30)
amp = 0.5  # Amplitude of the wave
freq = 0.5  # Frequency of the wave
phase = 0.0  # Phase shift of the wave
cam_dist = 10.0 # Camera distance from the wave
pitch = 0.1  # Pitch rotation
yaw = 0.1  # Yaw rotation

while(True):
    phase += 0.05  # Increment phase for animation
    if phase > 2 * math.pi:
        phase -= 2 * math.pi  # Reset phase to keep it within bounds
    if processKey():
        break
    draw_wave(amp, freq, phase, cam_dist, pitch, yaw)
    terminal.wr("\x1b[40;1HPress \'E\' to break...")
    display.show(0)  # show in manual refresh mode
    #time.sleep(0.03)


#terminal.wr("\x1b[40;1HPress any key to continue...")
#terminal.rd()
#del WIDTH, HEIGHT, GRID, GRID_POINTS, HALF_WIDTH, HALF_HEIGHT, FOCAL_LEN, MAX_COLOR
#del VIEWPORT_MIN_X, VIEWPORT_MAX_X, VIEWPORT_MIN_Y, VIEWPORT_MAX_Y
#del fast_sin, depth_sort, transform_points, draw_wave
#del coords, grid_x, grid_y, grid_r
#del proj_x, proj_y, proj_size, proj_depth, proj_color, proj_visible
#del draw_order, sort_keys, sin_lut
#del temp, amp, freq, phase, cam_dist, pitch, yaw
#del color_lut,gamma
gc.collect()  # Run garbage collector to free up memory
terminal.recoverRefresh()
display.fill(0) #clean the screen
display.restLUT()
terminal.wr("\x1b[2J\x1b[H")#move the cursor to the top, and clear the terminal buffer

terminal.wr("\x1b[?25h")  # show cursor