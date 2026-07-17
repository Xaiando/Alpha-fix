import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img_in = cv2.imread(file_path)
h, w = img_in.shape[:2]

# Optimal parameters found by hierarchical search
size = 25.6
off_x = 25.0
off_y = -0.6

y_all, x_all = np.indices((h, w))
phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2

# Recalculate colors based on TOP-LEFT corner ONLY (since it is guaranteed background)
corner_w = 64
tl_mask = np.zeros((h, w), dtype=bool)
tl_mask[:corner_w, :corner_w] = True

corner_bgr_pixels = img_in[tl_mask]
corner_phases = phase_all[tl_mask]

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

# Check dist_blur in bottom-left corner (y=1000..1009, x=0..9)
print("Bottom-left corner 10x10 patch distance values:")
for y in range(1000, 1010):
    row_vals = [f"{dist_blur[y, x]:5.2f}" for x in range(10)]
    print(" ".join(row_vals))

bl_corner = dist_blur[-50:, :50]
print("\nBottom-left corner distance statistics:")
print("  Min dist:", bl_corner.min())
print("  Max dist:", bl_corner.max())
print("  Mean dist:", bl_corner.mean())

# Check transparent count at pixel level
low, high = 15.0, 25.0
t = np.clip((dist_blur - low) / (high - low + 1e-6), 0.0, 1.0)
alpha_pixel = t * t * (3.0 - 2.0 * t)
print("\nPixel-level transparent count (alpha < 0.5):", np.sum(alpha_pixel < 0.5))

# Check cell grid means and classification
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

kernel = np.ones((3, 3), dtype=np.uint8)
grid_max_neighbor = cv2.dilate(grid_mean, kernel)
is_bg_cell = (grid_max_neighbor < high).astype(np.uint8)
near_bg_cell = cv2.dilate(is_bg_cell, kernel)
near_bg_smooth = cv2.resize(near_bg_cell.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
alpha = near_bg_smooth * alpha_pixel + (1.0 - near_bg_smooth) * 1.0

print(f"Background cells (is_bg_cell == 1): {np.sum(is_bg_cell == 1)} / {grid_mean.size}")
print("Final transparent count (alpha < 0.5):", np.sum(alpha < 0.5))

# Save the resulting alpha channel
cv2.imwrite("scratch/grateful_alpha_perfect_2.png", (alpha * 255.0).astype(np.uint8))
print("Saved final alpha map to scratch/grateful_alpha_perfect_2.png")
