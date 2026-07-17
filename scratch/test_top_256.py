import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Use top corners of size 256x256
corner_w = 256
top_mask = np.zeros((h, w), dtype=bool)
top_mask[:corner_w, :corner_w] = True
top_mask[:corner_w, -corner_w:] = True

top_pixels = gray[top_mask]
pixel_data = top_pixels.astype(np.float32).reshape(-1, 1)

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
_, _, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
c1, c2 = float(centers[0][0]), float(centers[1][0])
color_min = min(c1, c2)
color_max = max(c1, c2)

y_top, x_top = np.where(top_mask)
top_vals = gray[top_mask].astype(np.float32)

best_score = -1.0
best_size = 16.0
best_off_x = 0.0
best_off_y = 0.0

# Coarse search
for size in range(4, 65):
    step = max(1, size // 8)
    for off_x in range(0, size, step):
        for off_y in range(0, size, step):
            phase = (np.floor((x_top - off_x) / size) + np.floor((y_top - off_y) / size)) % 2
            expected = np.where(phase == 0, color_min, color_max)
            mae = np.mean(np.abs(top_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > best_score:
                best_score = score
                best_size = float(size)
                best_off_x = float(off_x)
                best_off_y = float(off_y)

print(f"Coarse search: size={best_size}, offset=({best_off_x}, {best_off_y}), MAE={1.0/best_score:.4f}")

# Refined float search on top 256x256 corners
refined_best_score = best_score
refined_size = best_size
refined_off_x = best_off_x
refined_off_y = best_off_y

for size_f in np.arange(best_size - 1.5, best_size + 1.6, 0.01):
    if size_f < 4:
        continue
    for off_x_f in np.arange(best_off_x - 1.5, best_off_x + 1.6, 0.5):
        for off_y_f in np.arange(best_off_y - 1.5, best_off_y + 1.6, 0.5):
            phase = (np.floor((x_top - off_x_f) / size_f) + np.floor((y_top - off_y_f) / size_f)) % 2
            expected = np.where(phase == 0, color_min, color_max)
            mae = np.mean(np.abs(top_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > refined_best_score:
                refined_best_score = score
                refined_size = size_f
                refined_off_x = off_x_f
                refined_off_y = off_y_f

print(f"Refined search: size={refined_size:.4f}, offset=({refined_off_x:.2f}, {refined_off_y:.2f}), MAE={1.0/refined_best_score:.4f}")
