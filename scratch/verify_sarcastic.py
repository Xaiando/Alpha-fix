import cv2
import numpy as np

img = cv2.imread(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\processed\emoji_sarcastic_png.png", cv2.IMREAD_UNCHANGED)
h, w, c = img.shape
print(f"Image shape: {h}x{w}x{c}")

# Check corners (should be fully transparent, alpha == 0)
corners = [
    img[0, 0],
    img[0, w-1],
    img[h-1, 0],
    img[h-1, w-1]
]
print("Corners (RGBA):")
for i, corner in enumerate(corners):
    print(f"  Corner {i}: {corner}")

# Check center 200x200 patch (should be fully opaque, alpha == 255)
center_patch = img[h//2-100:h//2+100, w//2-100:w//2+100, 3]
min_center_alpha = np.min(center_patch)
max_center_alpha = np.max(center_patch)
opaque_ratio = np.mean(center_patch == 255)
print(f"Center 200x200 alpha: min={min_center_alpha}, max={max_center_alpha}, opaque_ratio={opaque_ratio:.2%}")
