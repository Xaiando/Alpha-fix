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

# Pixel-level alpha
low, high = 15.0, 25.0
t = np.clip((dist_blur - low) / (high - low + 1e-6), 0.0, 1.0)
alpha_pixel = t * t * (3.0 - 2.0 * t)

print("Method 4 (Pixel-level only, no cell forcing):")
print("  Transparent pixels (alpha < 0.5):", np.sum(alpha_pixel < 0.5))

# Let's save Method 4 alpha map
cv2.imwrite("scratch/grateful_alpha_pixel_only.png", (alpha_pixel * 255.0).astype(np.uint8))
print("Saved Method 4 alpha map to scratch/grateful_alpha_pixel_only.png")
