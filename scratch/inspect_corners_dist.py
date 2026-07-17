import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img_in = cv2.imread(file_path)
h, w = img_in.shape[:2]
gray = cv2.cvtColor(img_in, cv2.COLOR_BGR2GRAY)

size = 25.6000
off_x = 25.00
off_y = -0.60

y_all, x_all = np.indices((h, w))
phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2

corner_w = 64
tl_mask = np.zeros((h, w), dtype=bool)
tl_mask[:corner_w, :corner_w] = True

corner_bgr_pixels = img_in[tl_mask]
corner_phases = phase_all[tl_mask]

p0_pixels = corner_bgr_pixels[corner_phases == 0]
p1_pixels = corner_bgr_pixels[corner_phases == 1]
color1_bgr = np.mean(p0_pixels, axis=0) if len(p0_pixels) > 0 else np.array([120.0, 120.0, 120.0])
color2_bgr = np.mean(p1_pixels, axis=0) if len(p1_pixels) > 0 else np.array([180.0, 180.0, 180.0])

print("Expected colors:")
print("  color1:", color1_bgr)
print("  color2:", color2_bgr)

expected_bg = np.zeros_like(img_in, dtype=np.float32)
expected_bg[phase_all == 0] = color1_bgr
expected_bg[phase_all == 1] = color2_bgr

diff = img_in.astype(np.float32) - expected_bg
dist = np.sqrt(np.sum(diff * diff, axis=-1))
dist_blur = cv2.GaussianBlur(dist, (5, 5), 0)

corners = {
    "top-left": dist_blur[:corner_w, :corner_w],
    "top-right": dist_blur[:corner_w, -corner_w:],
    "bottom-left": dist_blur[-corner_w:, :corner_w],
    "bottom-right": dist_blur[-corner_w:, -corner_w:],
}

for name, patch in corners.items():
    print(f"\n--- {name} corner dist ---")
    print("Min:", patch.min(), "Max:", patch.max(), "Mean:", patch.mean())
