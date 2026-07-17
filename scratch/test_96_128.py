import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def detect_grid(img, corner_w):
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    top_mask = np.zeros((h, w), dtype=bool)
    top_mask[:corner_w, :corner_w] = True
    top_mask[:corner_w, -corner_w:] = True
    
    top_pixels = gray[top_mask]
    if len(top_pixels) == 0:
        return 999.0, 16.0, 0.0
    
    pixel_data = top_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    
    y_top, x_top = np.where(top_mask)
    top_vals = gray[top_mask].astype(np.float32)
    
    best_score = -1.0
    best_size = 16.0
    best_off_x = 0.0
    best_off_y = 0.0
    
    for s in range(4, 65):
        step = max(1, s // 8)
        for ox in range(0, s, step):
            for oy in range(0, s, step):
                phase = (np.floor((x_top - ox) / s) + np.floor((y_top - oy) / s)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(top_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > best_score:
                    best_score = score
                    best_size = float(s)
                    best_off_x = float(ox)
                    best_off_y = float(oy)
                    
    # Stage 1 fine
    s1_score = best_score
    s1_size = best_size
    s1_ox = best_off_x
    s1_oy = best_off_y
    for sf in np.arange(best_size - 1.5, best_size + 1.6, 0.1):
        if sf < 4: continue
        for oxf in np.arange(best_off_x - 4.0, best_off_x + 4.1, 1.0):
            for oyf in np.arange(best_off_y - 4.0, best_off_y + 4.1, 1.0):
                phase = (np.floor((x_top - oxf) / sf) + np.floor((y_top - oyf) / sf)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(top_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > s1_score:
                    s1_score, s1_size, s1_ox, s1_oy = score, sf, oxf, oyf
                    
    # Stage 2 fine
    f_score = s1_score
    f_size = s1_size
    f_ox = s1_ox
    f_oy = s1_oy
    for sf in np.arange(s1_size - 0.15, s1_size + 0.16, 0.01):
        if sf < 4: continue
        for oxf in np.arange(s1_ox - 1.0, s1_ox + 1.1, 0.2):
            for oyf in np.arange(s1_oy - 1.0, s1_oy + 1.1, 0.2):
                phase = (np.floor((x_top - oxf) / sf) + np.floor((y_top - oyf) / sf)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(top_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > f_score:
                    f_score, f_size, f_ox, f_oy = score, sf, oxf, oyf
                    
    return 1.0 / f_score, f_size, color_max - color_min, (f_ox, f_oy)

test_files = ["emoji_party.jpg", "emoji_waving.jpg", "emoji_thinking_29.jpg"]
corner_widths = [96, 128]

for f in test_files:
    img = cv2.imread(str(src_dir / f))
    if img is None:
        continue
    h, w = img.shape[:2]
    print(f"\n===== File: {f} ({w}x{h}) =====")
    for cw in corner_widths:
        mae, size, diff, offset = detect_grid(img, cw)
        print(f"Mask {cw}: size={size:.4f}, offset=({offset[0]:.2f}, {offset[1]:.2f}), MAE={mae:.2f}, diff={diff:.2f}")
