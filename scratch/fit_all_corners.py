import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Use all 4 corners
corner_w = min(64, h // 4, w // 4)
mask = np.zeros((h, w), dtype=bool)
mask[:corner_w, :corner_w] = True
mask[:corner_w, -corner_w:] = True
mask[-corner_w:, :corner_w] = True
mask[-corner_w:, -corner_w:] = True

corner_pixels = gray[mask]
pixel_data = corner_pixels.astype(np.float32).reshape(-1, 1)

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
_, _, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
c1, c2 = float(centers[0][0]), float(centers[1][0])
color_min = min(c1, c2)
color_max = max(c1, c2)

y_indices, x_indices = np.where(mask)
corner_vals = gray[mask].astype(np.float32)

best_score = -1.0
best_size = 16.0
best_off_x = 0.0
best_off_y = 0.0

# 1. Coarse search over integer sizes
for size in range(4, 65):
    step = max(1, size // 8)
    for off_x in range(0, size, step):
        for off_y in range(0, size, step):
            phase = (np.floor((x_indices - off_x) / size) + np.floor((y_indices - off_y) / size)) % 2
            expected = np.where(phase == 0, color_min, color_max)
            mae = np.mean(np.abs(corner_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > best_score:
                best_score = score
                best_size = float(size)
                best_off_x = float(off_x)
                best_off_y = float(off_y)

print(f"Coarse search (4 corners): size={best_size}, offset=({best_off_x}, {best_off_y}), MAE={1.0/best_score:.4f}")

# 2. Refined float search
refined_best_score = best_score
refined_size = best_size
refined_off_x = best_off_x
refined_off_y = best_off_y

# Search sizes in steps of 0.05
for size_f in np.arange(best_size - 1.5, best_size + 1.6, 0.05):
    if size_f < 4:
        continue
    for off_x_f in np.arange(best_off_x - 2.0, best_off_x + 2.1, 0.5):
        for off_y_f in np.arange(best_off_y - 2.0, best_off_y + 2.1, 0.5):
            phase = (np.floor((x_indices - off_x_f) / size_f) + np.floor((y_indices - off_y_f) / size_f)) % 2
            expected = np.where(phase == 0, color_min, color_max)
            mae = np.mean(np.abs(corner_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > refined_best_score:
                refined_best_score = score
                refined_size = size_f
                refined_off_x = off_x_f
                refined_off_y = off_y_f

print(f"Refined search (4 corners): size={refined_size:.4f}, offset=({refined_off_x:.1f}, {refined_off_y:.1f}), MAE={1.0/refined_best_score:.4f}")
