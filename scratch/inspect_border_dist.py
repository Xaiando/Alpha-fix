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

# Check dist_blur values along the 4 edges of the image
print("Top edge dist_blur (first 20 pixels):", dist_blur[0, :20])
print("Bottom edge dist_blur (first 20 pixels):", dist_blur[-1, :20])
print("Left edge dist_blur (first 20 pixels):", dist_blur[:20, 0])
print("Right edge dist_blur (first 20 pixels):", dist_blur[:20, -1])

# Is the checkerboard pattern distorted or different near the borders?
# Let's count how many pixels near the border are within checkerboard range (dist_blur < 15)
border_width = 30
border_mask = np.zeros((h, w), dtype=bool)
border_mask[:border_width, :] = True
border_mask[-border_width:, :] = True
border_mask[:, :border_width] = True
border_mask[:, -border_width:] = True

print(f"\nWithin {border_width}px border:")
print(f"  Total pixels: {np.sum(border_mask)}")
print(f"  Pixels with dist_blur < 15: {np.sum((dist_blur < 15) & border_mask)}")
print(f"  Pixels with dist_blur >= 25: {np.sum((dist_blur >= 25) & border_mask)}")
print(f"  Pixels with 15 <= dist_blur < 25: {np.sum((dist_blur >= 15) & (dist_blur < 25) & border_mask)}")
