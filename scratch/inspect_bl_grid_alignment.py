import cv2
import numpy as np

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Parameters from Top Corners fit
size = 25.6000
off_x = 25.00
off_y = -0.60

# Let's generate expected background
y_all, x_all = np.indices((h, w))
phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2

color_min = 143.4
color_max = 188.3

expected = np.where(phase_all == 0, color_min, color_max)
diff = np.abs(gray.astype(np.float32) - expected)

# Bottom-left patch
patch_y0, patch_y1 = 900, 1024
patch_x0, patch_x1 = 0, 150

patch_gray = gray[patch_y0:patch_y1, patch_x0:patch_x1]
patch_diff = diff[patch_y0:patch_y1, patch_x0:patch_x1]

# Filter pixels that are close to checkerboard colors
bg_mask = (np.abs(patch_gray - color_min) < 15.0) | (np.abs(patch_gray - color_max) < 15.0)

print(f"Total patch pixels: {patch_gray.size}")
print(f"BG-like pixels in patch: {np.sum(bg_mask)}")

if np.sum(bg_mask) > 0:
    mae_bg = np.mean(patch_diff[bg_mask])
    print(f"MAE on BG-like pixels in BL corner: {mae_bg:.4f}")
    
    # Let's also print the first few rows/cols of patch_gray and phase_all
    print("\nSample BG-like pixels gray values vs expected vs phase:")
    count = 0
    for r in range(patch_y1 - patch_y0):
        for c in range(patch_x1 - patch_x0):
            if bg_mask[r, c] and count < 10:
                y = patch_y0 + r
                x = patch_x0 + c
                print(f"  y={y}, x={x}: gray={gray[y,x]}, expected={expected[y,x]:.1f}, phase={phase_all[y,x]}, diff={diff[y,x]:.1f}")
                count += 1
else:
    print("No BG-like pixels found in patch!")
