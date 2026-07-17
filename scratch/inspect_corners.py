import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

img = cv2.imread(str(src_dir / "emoji_thinking_29.jpg"))
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

print("BL Corner (bottom-left 5x5):")
print(gray[h-5:, :5])

print("\nBR Corner (bottom-right 5x5):")
print(gray[h-5:, w-5:])

print("\nTL Corner (top-left 5x5):")
print(gray[:5, :5])

print("\nTR Corner (top-right 5x5):")
print(gray[:5, w-5:])
