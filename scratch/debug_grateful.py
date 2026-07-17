import cv2
import numpy as np
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.pipeline import AlphaFix2Processor

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img_in = cv2.imread(file_path)

config = AlphaFix2Config(
    mode="overlay",
    overlay_method="checkerboard",
    checkerboard_low=15.0,
    checkerboard_high=25.0,
    checkerboard_size=0,
    checkerboard_offset_x=-1,
    checkerboard_offset_y=-1,
    export_alpha_matte=True
)

processor = AlphaFix2Processor(config)
result = processor.process_frame(img_in)

# Let's inspect the checkerboard params detected
params = processor._checkerboard_params
print("Detected checkerboard params:")
for k, v in params.items():
    print(f"  {k}: {v}")

# Now let's calculate dist ourselves to see what is going on
h, w = img_in.shape[:2]
gray = cv2.cvtColor(img_in, cv2.COLOR_BGR2GRAY)
size = params["size"]
off_x = params["offset_x"]
off_y = params["offset_y"]
color1_bgr = params["color1_bgr"]
color2_bgr = params["color2_bgr"]

y_all, x_all = np.indices((h, w))
phase_all = (((x_all - off_x) // size) + ((y_all - off_y) // size)) % 2

expected_bg = np.zeros_like(img_in, dtype=np.float32)
expected_bg[phase_all == 0] = color1_bgr
expected_bg[phase_all == 1] = color2_bgr

diff = img_in.astype(np.float32) - expected_bg
dist = np.sqrt(np.sum(diff * diff, axis=-1))
dist_blur = cv2.GaussianBlur(dist, (5, 5), 0)

# Check corner dist values
corner_dist = dist_blur[:50, :50]
print("\nTop-left corner distance statistics:")
print("  Min dist:", corner_dist.min())
print("  Max dist:", corner_dist.max())
print("  Mean dist:", corner_dist.mean())
print("  Std dist:", np.std(corner_dist))

# Check cell_guided values
cell_x = (x_all - off_x) // size
cell_y = (y_all - off_y) // size
min_cx = np.min(cell_x)
min_cy = np.min(cell_y)
cell_x_idx = cell_x - min_cx
cell_y_idx = cell_y - min_cy
num_cx = np.max(cell_x_idx) + 1
num_cy = np.max(cell_y_idx) + 1

cell_sum = np.zeros((num_cy, num_cx), dtype=np.float32)
cell_count = np.zeros((num_cy, num_cx), dtype=np.float32)
np.add.at(cell_sum, (cell_y_idx, cell_x_idx), dist)
np.add.at(cell_count, (cell_y_idx, cell_x_idx), 1.0)
grid_mean = cell_sum / np.maximum(cell_count, 1.0)

kernel = np.ones((3, 3), dtype=np.uint8)
grid_max_neighbor = cv2.dilate(grid_mean, kernel)
is_bg_cell = (grid_max_neighbor < config.checkerboard_low).astype(np.uint8)

print("\nCell classification:")
print("  Total cells:", grid_mean.size)
print("  Background cells (is_bg_cell == 1):", np.sum(is_bg_cell == 1))
print("  Min grid_max_neighbor in corner:", grid_max_neighbor[0:2, 0:2])
print("  Min grid_mean in corner:", grid_mean[0:2, 0:2])
