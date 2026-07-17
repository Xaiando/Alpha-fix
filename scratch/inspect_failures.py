import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
failed_names = [
    "emoji_detective.jpg",
    "emoji_got_it_cool_32.png",
    "emoji_mindblown.jpg",
    "emoji_salute_1.jpg",
    "emoji_sleeping_1.jpg",
    "emoji_tired_salute.png",
    "emoji_wink.jpg",
    "gao8bEg - Imgur(1).png",
    "teledra-emoji-fight-cute.jpg",
    "teledra-emoji-fight-you.jpg"
]

for name in failed_names:
    p = src_dir / name
    if not p.exists():
        print(f"{name} does not exist in src_dir")
        continue
    img = cv2.imread(str(p))
    if img is None:
        print(f"{name} cannot be read")
        continue
    h, w = img.shape[:2]
    # Check if there is an alpha channel in the original (for PNGs)
    orig_has_alpha = False
    if p.suffix.lower() == ".png":
        img_u = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
        if img_u is not None and img_u.shape[2] == 4:
            orig_has_alpha = np.any(img_u[:, :, 3] < 255)
    
    print(f"{name}: shape={img.shape}, orig_has_alpha={orig_has_alpha}")
