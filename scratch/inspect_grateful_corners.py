import cv2
import numpy as np

img = cv2.imread(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

h, w = gray.shape
print(f"Image shape: {w}x{h}")

corners = {
    "top-left": gray[:50, :50],
    "top-right": gray[:50, -50:],
    "bottom-left": gray[-50:, :50],
    "bottom-right": gray[-50:, -50:]
}

for name, patch in corners.items():
    print(f"\n--- {name} corner ---")
    print("Unique values:", np.unique(patch))
    print("Standard deviation:", np.std(patch))
    print("Mean value:", np.mean(patch))
