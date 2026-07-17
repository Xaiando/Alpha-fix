import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def fit_single_corner(fname, corner_name):
    img = cv2.imread(str(src_dir / fname))
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    corner_w = 96
    mask = np.zeros((h, w), dtype=bool)
    if corner_name == "TL":
        mask[:corner_w, :corner_w] = True
    elif corner_name == "TR":
        mask[:corner_w, -corner_w:] = True
    elif corner_name == "BL":
        mask[-corner_w:, :corner_w] = True
    elif corner_name == "BR":
        mask[-corner_w:, -corner_w:] = True
        
    pixel_data = gray[mask].astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min, color_max = min(c1, c2), max(c1, c2)
    
    y_indices, x_indices = np.where(mask)
    vals = gray[mask].astype(np.float32)
    
    best_score = -1.0
    best_size = 16.0
    best_ox, best_oy = 0.0, 0.0
    
    # Grid search for size between 24.0 and 27.0
    for s in np.arange(24.0, 27.1, 0.1):
        for ox in np.arange(0.0, s, 2.0):
            for oy in np.arange(0.0, s, 2.0):
                phase = (np.floor((x_indices - ox) / s) + np.floor((y_indices - oy) / s)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > best_score:
                    best_score = score
                    best_size = s
                    best_ox = ox
                    best_oy = oy
                    
    # Fine float fit
    f_score = best_score
    f_size = best_size
    f_ox = best_ox
    f_oy = best_oy
    for s_f in np.arange(best_size - 0.15, best_size + 0.16, 0.01):
        for ox_f in np.arange(best_ox - 1.0, best_ox + 1.1, 0.2):
            for oy_f in np.arange(best_oy - 1.0, best_oy + 1.1, 0.2):
                phase = (np.floor((x_indices - ox_f) / s_f) + np.floor((y_indices - oy_f) / s_f)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > f_score:
                    f_score = score
                    f_size = s_f
                    f_ox = ox_f
                    f_oy = oy_f
                    
    print(f"Corner {corner_name}: size={f_size:.4f}, offset=({f_ox:.2f}, {f_oy:.2f}), MAE={1.0/f_score:.2f}, diff={color_max - color_min:.1f}")

print("===== emoji_thinking_29.jpg =====")
for c in ["TL", "TR", "BL", "BR"]:
    fit_single_corner("emoji_thinking_29.jpg", c)

print("\n===== emoji_waving.jpg =====")
for c in ["TL", "TR", "BL", "BR"]:
    fit_single_corner("emoji_waving.jpg", c)
