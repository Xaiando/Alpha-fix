import cv2
import numpy as np
from pathlib import Path

p = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_mindblown.jpg")
img = cv2.imread(str(p))
if img is not None:
    print("Top-left 5x5 BGR values:")
    for y in range(5):
        row_strs = []
        for x in range(5):
            row_strs.append(f"{img[y, x]}")
        print("  ".join(row_strs))
else:
    print("Cannot read image")
