import cv2
import numpy as np

# Load the binarized mask
# mask = 1 where alpha_pixel < 0.5, 0 otherwise
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
transparent_mask = (alpha_pixel < 0.5).astype(np.uint8)

# Check borders
top_border = transparent_mask[0, :]
bottom_border = transparent_mask[-1, :]
left_border = transparent_mask[:, 0]
right_border = transparent_mask[:, -1]

print("Transparent pixel count on borders:")
print("  Top:", np.sum(top_border == 1), "/", w)
print("  Bottom:", np.sum(bottom_border == 1), "/", w)
print("  Left:", np.sum(left_border == 1), "/", h)
print("  Right:", np.sum(right_border == 1), "/", h)

# Let's see if the flood fill connected to the borders
padded = np.pad(transparent_mask, 1, mode='constant', constant_values=1)
h_pad, w_pad = padded.shape
flood_filled = padded.copy()
mask_ff = np.zeros((h_pad + 2, w_pad + 2), dtype=np.uint8)
cv2.floodFill(flood_filled, mask_ff, (0, 0), 0)
internal_holes = flood_filled[1:-1, 1:-1]

# Where are the internal holes located?
# Let's count where they are (y-coordinates)
y_coords, x_coords = np.where(internal_holes)
print(f"Holes range: y=[{y_coords.min() if len(y_coords) > 0 else 'N/A'}, {y_coords.max() if len(y_coords) > 0 else 'N/A'}], x=[{x_coords.min() if len(x_coords) > 0 else 'N/A'}, {x_coords.max() if len(x_coords) > 0 else 'N/A'}]")
