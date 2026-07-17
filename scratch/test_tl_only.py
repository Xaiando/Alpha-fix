import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img_in = cv2.imread(file_path)
h, w = img_in.shape[:2]

# Parameters found by top 256x256 corners fit
size = 25.68
off_x = 22.5
off_y = -1.0

y_all, x_all = np.indices((h, w))
phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2

# Recalculate colors based on TOP-LEFT corner ONLY
corner_w = 64
tl_mask = np.zeros((h, w), dtype=bool)
tl_mask[:corner_w, :corner_w] = True

corner_bgr_pixels = img_in[tl_mask]
corner_phases = phase_all[tl_mask]

p0_pixels = corner_bgr_pixels[corner_phases == 0]
p1_pixels = corner_bgr_pixels[corner_phases == 1]
color1_bgr = np.mean(p0_pixels, axis=0) if len(p0_pixels) > 0 else np.array([120.0, 120.0, 120.0])
color2_bgr = np.mean(p1_pixels, axis=0) if len(p1_pixels) > 0 else np.array([180.0, 180.0, 180.0])

print("Detected colors from top-left only:")
print("  color1_bgr:", color1_bgr)
print("  color2_bgr:", color2_bgr)

expected_bg = np.zeros_like(img_in, dtype=np.float32)
expected_bg[phase_all == 0] = color1_bgr
expected_bg[phase_all == 1] = color2_bgr

diff = img_in.astype(np.float32) - expected_bg
dist = np.sqrt(np.sum(diff * diff, axis=-1))
dist_blur = cv2.GaussianBlur(dist, (5, 5), 0)

# Check dist_blur in bottom-left corner
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
