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

# We want to fill holes in alpha_pixel.
# A hole is a region of low alpha (transparent) that is not connected to the image border.
# Let's binarize alpha_pixel: mask = 1 where alpha_pixel is transparent, 0 where opaque.
transparent_mask = (alpha_pixel < 0.5).astype(np.uint8)

# Flood fill from the borders of transparent_mask.
# To do this easily, we can pad the mask by 1 pixel of 1s (transparent) and flood fill from (0,0) with 0.
padded = np.pad(transparent_mask, 1, mode='constant', constant_values=1)
h_pad, w_pad = padded.shape

# Flood fill from (0,0) on the padded mask.
# This will find all transparent pixels connected to the borders.
flood_filled = padded.copy()
mask_ff = np.zeros((h_pad + 2, w_pad + 2), dtype=np.uint8)
cv2.floodFill(flood_filled, mask_ff, (0, 0), 0)

# The remaining 1s in flood_filled are the internal holes.
internal_holes_padded = flood_filled
internal_holes = internal_holes_padded[1:-1, 1:-1]

# Fill the holes by setting alpha to 1.0 in those regions
alpha_filled = alpha_pixel.copy()
alpha_filled[internal_holes == 1] = 1.0

print("Pixel-level transparent count:", np.sum(alpha_pixel < 0.5))
print("Flood-fill filled transparent count:", np.sum(alpha_filled < 0.5))
print("Holes filled (pixels):", np.sum(internal_holes == 1))

cv2.imwrite("scratch/grateful_alpha_filled.png", (alpha_filled * 255.0).astype(np.uint8))
print("Saved filled alpha map to scratch/grateful_alpha_filled.png")
