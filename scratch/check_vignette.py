import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def check_colors(fname, size, off_x, off_y):
    img = cv2.imread(str(src_dir / fname))
    h, w = img.shape[:2]
    
    y_all, x_all = np.indices((h, w))
    phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2
    
    corner_w = 96
    corners = {
        "TL": (0, corner_w, 0, corner_w),
        "TR": (0, corner_w, w - corner_w, w),
        "BL": (h - corner_w, h, 0, corner_w),
        "BR": (h - corner_w, h, w - corner_w, w)
    }
    
    print(f"\n--- Colors for {fname} ---")
    for name, (r0, r1, c0, c1) in corners.items():
        mask = np.zeros((h, w), dtype=bool)
        mask[r0:r1, c0:c1] = True
        
        pixels = img[mask]
        phases = phase_all[mask]
        
        p0 = pixels[phases == 0]
        p1 = pixels[phases == 1]
        
        c0_mean = np.mean(p0, axis=0) if len(p0) > 0 else np.array([0,0,0])
        c1_mean = np.mean(p1, axis=0) if len(p1) > 0 else np.array([0,0,0])
        diff = np.linalg.norm(c1_mean - c0_mean)
        print(f"  Corner {name}: color0={c0_mean.round(1)}, color1={c1_mean.round(1)}, diff={diff:.2f}")

check_colors("emoji_waving.jpg", 25.6000, 24.60, 24.60)
check_colors("emoji_thinking_29.jpg", 25.6000, 24.60, 24.60)
