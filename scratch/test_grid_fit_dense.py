import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def test_file(fname):
    img = cv2.imread(str(src_dir / fname))
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    corner_w = 96
    mask = np.zeros((h, w), dtype=bool)
    mask[:corner_w, :corner_w] = True
    mask[:corner_w, -corner_w:] = True
    mask[-corner_w:, :corner_w] = True
    mask[-corner_w:, -corner_w:] = True
    
    pixel_data = gray[mask].astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min, color_max = min(c1, c2), max(c1, c2)
    
    y_indices, x_indices = np.where(mask)
    vals = gray[mask].astype(np.float32)
    
    best_mae = 999.0
    best_size = 0.0
    best_ox, best_oy = 0.0, 0.0
    
    # We will search size from 25.40 to 25.80 with step 0.002
    # And offsets from 0 to size with step 1.0
    for s in np.arange(25.40, 25.80, 0.002):
        for ox in np.arange(0.0, s, 1.0):
            for oy in np.arange(0.0, s, 1.0):
                phase = (np.floor((x_indices - ox) / s) + np.floor((y_indices - oy) / s)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                if mae < best_mae:
                    best_mae = mae
                    best_size = s
                    best_ox = ox
                    best_oy = oy
                    
    print(f"\nDense Fit for {fname}:")
    print(f"  Size: {best_size:.4f}, offset: ({best_ox:.2f}, {best_oy:.2f}), MAE: {best_mae:.3f}")
    
    # Also print MAE in each corner for this best fit
    corners = {
        "TL": (y_indices < corner_w) & (x_indices < corner_w),
        "TR": (y_indices < corner_w) & (x_indices >= w - corner_w),
        "BL": (y_indices >= h - corner_w) & (x_indices < corner_w),
        "BR": (y_indices >= h - corner_w) & (x_indices >= w - corner_w)
    }
    
    phase_best = (np.floor((x_indices - best_ox) / best_size) + np.floor((y_indices - best_oy) / best_size)) % 2
    expected_best = np.where(phase_best == 0, color_min, color_max)
    for name, c_mask in corners.items():
        c_mae = np.mean(np.abs(vals[c_mask] - expected_best[c_mask]))
        print(f"    Corner {name} MAE: {c_mae:.2f}")

test_file("emoji_waving.jpg")
test_file("emoji_thinking_29.jpg")
