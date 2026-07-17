import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img_in = cv2.imread(file_path)
h, w = img_in.shape[:2]

# Refined parameters
size = 25.6
off_x = -0.5
off_y = 24.5

# We must compute color1 and color2 for BGR using the float phases
y_all, x_all = np.indices((h, w))
phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2

# Recalculate colors based on corners with correct float phase
corner_w = min(64, h // 4, w // 4)
corner_mask = np.zeros((h, w), dtype=bool)
corner_mask[:corner_w, :corner_w] = True
corner_mask[:corner_w, -corner_w:] = True

corner_bgr_pixels = img_in[corner_mask]
corner_phases = phase_all[corner_mask]

p0_pixels = corner_bgr_pixels[corner_phases == 0]
p1_pixels = corner_bgr_pixels[corner_phases == 1]
color1_bgr = np.mean(p0_pixels, axis=0) if len(p0_pixels) > 0 else np.array([120.0, 120.0, 120.0])
color2_bgr = np.mean(p1_pixels, axis=0) if len(p1_pixels) > 0 else np.array([180.0, 180.0, 180.0])

expected_bg = np.zeros_like(img_in, dtype=np.float32)
expected_bg[phase_all == 0] = color1_bgr
expected_bg[phase_all == 1] = color2_bgr

diff = img_in.astype(np.float32) - expected_bg
dist = np.sqrt(np.sum(diff * diff, axis=-1))
dist_blur = cv2.GaussianBlur(dist, (5, 5), 0)

# Check dist_blur in bottom-left corner
bl_corner = dist_blur[-50:, :50]
print("Bottom-left corner distance statistics:")
print("  Min dist:", bl_corner.min())
print("  Max dist:", bl_corner.max())
print("  Mean dist:", bl_corner.mean())

# Pixel-level alpha
low, high = 15.0, 25.0
t = np.clip((dist_blur - low) / (high - low + 1e-6), 0.0, 1.0)
alpha_pixel = t * t * (3.0 - 2.0 * t)

print("\nPixel-level transparent count (alpha < 0.5):", np.sum(alpha_pixel < 0.5))

# Check cell grid means
cell_x = np.floor((x_all - off_x) / size)
cell_y = np.floor((y_all - off_y) / size)
min_cx = np.min(cell_x)
min_cy = np.min(cell_y)
cell_x_idx = (cell_x - min_cx).astype(np.int32)
cell_y_idx = (cell_y - min_cy).astype(np.int32)
num_cx = np.max(cell_x_idx) + 1
num_cy = np.max(cell_y_idx) + 1

cell_sum = np.zeros((num_cy, num_cx), dtype=np.float32)
cell_count = np.zeros((num_cy, num_cx), dtype=np.float32)
np.add.at(cell_sum, (cell_y_idx, cell_x_idx), dist_blur)
np.add.at(cell_count, (cell_y_idx, cell_x_idx), 1.0)
grid_mean = cell_sum / np.maximum(cell_count, 1.0)

# With correct size, check how many cells have mean < high
is_bg_cell = (grid_mean < 35.0).astype(np.uint8)
print("Cells with mean < 35.0:", np.sum(is_bg_cell == 1), "/", grid_mean.size)

# If we do the original Method 1 classification with the new parameters:
kernel = np.ones((3, 3), dtype=np.uint8)
grid_max_neighbor = cv2.dilate(grid_mean, kernel)
is_bg_cell_orig = (grid_max_neighbor < 20.0).astype(np.uint8) # use 20.0 to be safe
near_bg_cell_orig = cv2.dilate(is_bg_cell_orig, kernel)
near_bg_smooth_orig = cv2.resize(near_bg_cell_orig.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
alpha_orig = near_bg_smooth_orig * alpha_pixel + (1.0 - near_bg_smooth_orig) * 1.0
print("Orig Method 1 transparent count with float params:", np.sum(alpha_orig < 0.5))
