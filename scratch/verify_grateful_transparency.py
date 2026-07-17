import cv2
import numpy as np

img = cv2.imread(r"scratch/grateful_processed.png", cv2.IMREAD_UNCHANGED)
h, w, c = img.shape
print(f"Image shape: {w}x{h}x{c}")

# Check 4 corners (should be fully transparent, alpha == 0)
corners = {
    "top-left": img[0:10, 0:10, 3],
    "top-right": img[0:10, -10:, 3],
    "bottom-left": img[-10:, 0:10, 3],
    "bottom-right": img[-10:, -10:, 3]
}

for name, patch in corners.items():
    print(f"\n--- {name} corner alpha ---")
    print("Min:", patch.min(), "Max:", patch.max(), "Mean:", patch.mean())

# Check center 200x200 patch (should be opaque, alpha == 255)
center_patch = img[h//2-100:h//2+100, w//2-100:w//2+100, 3]
print("\n--- Center 200x200 alpha ---")
print("Min:", center_patch.min(), "Max:", center_patch.max(), "Opaque ratio:", np.mean(center_patch == 255))
