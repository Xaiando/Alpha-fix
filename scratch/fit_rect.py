import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def fit_rect_global(fname):
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
    
    # 1. Coarse search
    best_score = -1.0
    best_sx, best_sy = 16.0, 16.0
    best_ox, best_oy = 0.0, 0.0
    
    # Coarse search around 25.6
    for sx in np.arange(24.0, 27.1, 0.2):
        for sy in np.arange(24.0, 27.1, 0.2):
            step_x = max(1.0, sx / 4.0)
            step_y = max(1.0, sy / 4.0)
            for ox in np.arange(0.0, sx, step_x):
                for oy in np.arange(0.0, sy, step_y):
                    phase = (np.floor((x_indices - ox) / sx) + np.floor((y_indices - oy) / sy)) % 2
                    expected = np.where(phase == 0, color_min, color_max)
                    mae = np.mean(np.abs(vals - expected))
                    score = 1.0 / (mae + 1e-5)
                    if score > best_score:
                        best_score = score
                        best_sx, best_sy = sx, sy
                        best_ox, best_oy = ox, oy
                        
    # 2. Fine search Stage 1 (step 0.05)
    s1_score = best_score
    s1_sx, s1_sy = best_sx, best_sy
    s1_ox, s1_oy = best_ox, best_oy
    
    for sx in np.arange(best_sx - 0.3, best_sx + 0.31, 0.05):
        for sy in np.arange(best_sy - 0.3, best_sy + 0.31, 0.05):
            for ox in np.arange(best_ox - 1.0, best_ox + 1.1, 0.5):
                for oy in np.arange(best_oy - 1.0, best_oy + 1.1, 0.5):
                    phase = (np.floor((x_indices - ox) / sx) + np.floor((y_indices - oy) / sy)) % 2
                    expected = np.where(phase == 0, color_min, color_max)
                    mae = np.mean(np.abs(vals - expected))
                    score = 1.0 / (mae + 1e-5)
                    if score > s1_score:
                        s1_score = score
                        s1_sx, s1_sy = sx, sy
                        s1_ox, s1_oy = ox, oy
                        
    # 3. Fine search Stage 2 (step 0.01)
    f_score = s1_score
    f_sx, f_sy = s1_sx, s1_sy
    f_ox, f_oy = s1_ox, s1_oy
    
    for sx in np.arange(s1_sx - 0.06, s1_sx + 0.07, 0.01):
        for sy in np.arange(s1_sy - 0.06, s1_sy + 0.07, 0.01):
            for ox in np.arange(s1_ox - 0.4, s1_ox + 0.5, 0.1):
                for oy in np.arange(s1_oy - 0.4, s1_oy + 0.5, 0.1):
                    phase = (np.floor((x_indices - ox) / sx) + np.floor((y_indices - oy) / sy)) % 2
                    expected = np.where(phase == 0, color_min, color_max)
                    mae = np.mean(np.abs(vals - expected))
                    score = 1.0 / (mae + 1e-5)
                    if score > f_score:
                        f_score = score
                        f_sx, f_sy = sx, sy
                        f_ox, f_oy = ox, oy
                        
    print(f"\n===== Global Rectangular Fit for {fname} =====")
    print(f"  Best size_x: {f_sx:.4f}, size_y: {f_sy:.4f}")
    print(f"  Best offset: ({f_ox:.2f}, {f_oy:.2f})")
    print(f"  MAE: {1.0/f_score:.2f}")

fit_rect_global("emoji_waving.jpg")
fit_rect_global("emoji_thinking_29.jpg")
