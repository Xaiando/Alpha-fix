import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Use the same setup as in test_two_pass.py
top_w = min(64, h // 4, w // 4)
top_mask = np.zeros((h, w), dtype=bool)
top_mask[:top_w, :top_w] = True
top_mask[:top_w, -top_w:] = True

top_pixels = gray[top_mask]
pixel_data = top_pixels.astype(np.float32).reshape(-1, 1)

criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
_, _, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
c1, c2 = float(centers[0][0]), float(centers[1][0])
color_min = min(c1, c2)
color_max = max(c1, c2)

corner_w = min(128, h // 3, w // 3)
all_corners_mask = np.zeros((h, w), dtype=bool)
all_corners_mask[:corner_w, :corner_w] = True
all_corners_mask[:corner_w, -corner_w:] = True
all_corners_mask[-corner_w:, :corner_w] = True
all_corners_mask[-corner_w:, -corner_w:] = True

bg_pixel_mask = (np.abs(gray - color_min) < 15.0) | (np.abs(gray - color_max) < 15.0)
fit_mask = all_corners_mask & bg_pixel_mask

y_all, x_all = np.where(fit_mask)
corner_vals = gray[fit_mask].astype(np.float32)

def get_mae(size_f, off_x_f, off_y_f):
    phase = (np.floor((x_all - off_x_f) / size_f) + np.floor((y_all - off_y_f) / size_f)) % 2
    expected = np.where(phase == 0, color_min, color_max)
    return np.mean(np.abs(corner_vals - expected))

print("MAE of size=25.6, offset=(-0.5, 24.5):", get_mae(25.6, -0.5, 24.5))
print("MAE of size=26.74, offset=(0.0, 22.5):", get_mae(26.74, 0.0, 22.5))
print("MAE of size=25.68, offset=(-0.5, 24.5):", get_mae(25.68, -0.5, 24.5))
print("MAE of size=25.64, offset=(-0.5, 24.5):", get_mae(25.64, -0.5, 24.5))
print("MAE of size=25.65, offset=(-0.5, 24.5):", get_mae(25.65, -0.5, 24.5))

# Let's search over size_f for off_x_f = -0.5, off_y_f = 24.5
print("\nSearching size_f with fixed offset (-0.5, 24.5):")
best_m = 999.0
best_s = 25.0
for s in np.arange(25.0, 27.0, 0.01):
    m = get_mae(s, -0.5, 24.5)
    if m < best_m:
        best_m = m
        best_s = s
print(f"Best size found: {best_s:.4f} with MAE {best_m:.4f}")
