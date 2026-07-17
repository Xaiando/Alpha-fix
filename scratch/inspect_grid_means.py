import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img_in = cv2.imread(file_path)
h, w = img_in.shape[:2]

# Simulated detected parameters
size = 27
off_x = 0
off_y = 25
color1_bgr = np.array([145.95849609, 146.02978516, 145.8996582])
color2_bgr = np.array([186.29052734, 186.33496094, 186.30273438])

y_all, x_all = np.indices((h, w))
phase_all = (((x_all - off_x) // size) + ((y_all - off_y) // size)) % 2

expected_bg = np.zeros_like(img_in, dtype=np.float32)
expected_bg[phase_all == 0] = color1_bgr
expected_bg[phase_all == 1] = color2_bgr

diff = img_in.astype(np.float32) - expected_bg
dist = np.sqrt(np.sum(diff * diff, axis=-1))
dist_blur = cv2.GaussianBlur(dist, (5, 5), 0)

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
np.add.at(cell_sum, (cell_y_idx, cell_x_idx), dist_blur)
np.add.at(cell_count, (cell_y_idx, cell_x_idx), 1.0)
grid_mean = cell_sum / np.maximum(cell_count, 1.0)

# Sort all cell means to see their distribution
sorted_means = np.sort(grid_mean.flatten())
print("Percentiles of cell grid_mean:")
for p in [0, 5, 10, 15, 20, 25, 30, 40, 50, 75, 90, 100]:
    val = np.percentile(sorted_means, p)
    print(f"  {p}%: {val:.2f}")

# Let's count how many cells have mean < threshold
for thresh in [15, 20, 25, 30, 35, 40, 50, 60]:
    count = np.sum(grid_mean < thresh)
    pct = count / grid_mean.size
    print(f"  Cells with mean < {thresh}: {count} ({pct:.2%})")
