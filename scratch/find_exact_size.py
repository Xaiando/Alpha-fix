import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def fit_global(fname):
    img = cv2.imread(str(src_dir / fname))
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    corner_w = 96
    mask = np.zeros((h, w), dtype=bool)
    mask[:corner_w, :corner_w] = True
    mask[:corner_w, -corner_w:] = True
    mask[-corner_w:, :corner_w] = True
    mask[-corner_w:, -corner_w:] = True
    
    # Check standard deviation to see if we should skip some corners
    # (e.g. if a corner is blocked by subject).
    # For emoji_thinking_29, BL and BR corners had std=16.6, which is checkerboard.
    
    pixel_data = gray[mask].astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min, color_max = min(c1, c2), max(c1, c2)
    
    y_indices, x_indices = np.where(mask)
    vals = gray[mask].astype(np.float32)
    
    # Coarse search
    best_score = -1.0
    best_size = 16.0
    best_off_x = 0.0
    best_off_y = 0.0
    
    for s in range(4, 65):
        step = max(1, s // 8)
        for ox in range(0, s, step):
            for oy in range(0, s, step):
                phase = (np.floor((x_indices - ox) / s) + np.floor((y_indices - oy) / s)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > best_score:
                    best_score = score
                    best_size = float(s)
                    best_off_x = float(ox)
                    best_off_y = float(oy)
                    
    # Stage 1: Coarse float
    s1_score = best_score
    s1_size = best_size
    s1_ox = best_off_x
    s1_oy = best_off_y
    for sf in np.arange(best_size - 1.5, best_size + 1.6, 0.1):
        if sf < 4: continue
        for oxf in np.arange(best_off_x - 4.0, best_off_x + 4.1, 1.0):
            for oyf in np.arange(best_off_y - 4.0, best_off_y + 4.1, 1.0):
                phase = (np.floor((x_indices - oxf) / sf) + np.floor((y_indices - oyf) / sf)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > s1_score:
                    s1_score, s1_size, s1_ox, s1_oy = score, sf, oxf, oyf
                    
    # Stage 2: Fine float
    f_score = s1_score
    f_size = s1_size
    f_ox = s1_ox
    f_oy = s1_oy
    for sf in np.arange(s1_size - 0.15, s1_size + 0.16, 0.01):
        if sf < 4: continue
        for oxf in np.arange(s1_ox - 1.0, s1_ox + 1.1, 0.2):
            for oyf in np.arange(s1_oy - 1.0, s1_oy + 1.1, 0.2):
                phase = (np.floor((x_indices - oxf) / sf) + np.floor((y_indices - oyf) / sf)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > f_score:
                    f_score, f_size, f_ox, f_oy = score, sf, oxf, oyf
                    
    print(f"\n===== Global Fit for {fname} =====")
    print(f"  Best size: {f_size:.4f}")
    print(f"  Best offset: ({f_ox:.2f}, {f_oy:.2f})")
    print(f"  MAE: {1.0/f_score:.2f}")

fit_global("emoji_waving.jpg")
fit_global("emoji_thinking_29.jpg")
