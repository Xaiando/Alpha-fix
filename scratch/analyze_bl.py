import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
img = cv2.imread(str(src_dir / "emoji_thinking_29.jpg"))
h, w = img.shape[:2]
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

cw = 96
corners = {
    "TL": gray[:cw, :cw],
    "TR": gray[:cw, w-cw:],
    "BL": gray[h-cw:, :cw],
    "BR": gray[h-cw:, w-cw:]
}

for name, region in corners.items():
    print(f"Corner {name}: min={region.min()}, max={region.max()}, mean={region.mean():.1f}, std={region.std():.1f}")
