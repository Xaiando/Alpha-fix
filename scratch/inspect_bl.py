import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def fit_anisotropic(fname):
    img = cv2.imread(str(src_dir / fname))
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # We will sample all four corners for fitting, or just TL & TR & BL & BR
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
    
    best_score = -1.0
    best_sx, best_sy = 16.0, 16.0
    best_ox, best_oy = 0.0, 0.0
    
    # Coarse search
    for sx in range(16, 33):
        for sy in range(16, 33):
            # Check offsets in step size/4
            step_x = max(1, sx // 4)
            step_y = max(1, sy // 4)
            for ox in range(0, sx, step_x):
                for oy in range(0, sy, step_y):
                    phase = (np.floor((x_indices - ox) / sx) + np.floor((y_indices - oy) / sy)) % 2
                    expected = np.where(phase == 0, color_min, color_max)
                    mae = np.mean(np.abs(vals - expected))
                    score = 1.0 / (mae + 1e-5)
                    if score > best_score:
                        best_score = score
                        best_sx, best_sy = float(sx), float(sy)
                        best_ox, best_oy = float(ox), float(oy)
                        
    print(f"\n--- Anisotropic fit for {fname} ---")
    print(f"  Coarse best: size_x={best_sx}, size_y={best_sy}, offset=({best_ox}, {best_oy}), MAE={1.0/best_score:.2f}")
    
    # Fine float search around coarse
    f_score = best_score
    fsx, fsy = best_sx, best_sy
    fox, foy = best_ox, best_oy
    for sx_f in np.arange(best_sx - 1.0, best_sx + 1.1, 0.05):
        for sy_f in np.arange(best_sy - 1.0, best_sy + 1.1, 0.05):
            for ox_f in np.arange(best_ox - 1.5, best_ox + 1.6, 0.5):
                for oy_f in np.arange(best_oy - 1.5, best_oy + 1.6, 0.5):
                    phase = (np.floor((x_indices - ox_f) / sx_f) + np.floor((y_indices - oy_f) / sy_f)) % 2
                    expected = np.where(phase == 0, color_min, color_max)
                    mae = np.mean(np.abs(vals - expected))
                    score = 1.0 / (mae + 1e-5)
                    if score > f_score:
                        f_score = score
                        fsx, fsy = sx_f, sy_f
                        fox, foy = ox_f, oy_f
                        
    print(f"  Fine best: size_x={fsx:.4f}, size_y={fsy:.4f}, offset=({fox:.2f}, {foy:.2f}), MAE={1.0/f_score:.2f}")

fit_anisotropic("emoji_thinking_29.jpg")
fit_anisotropic("emoji_waving.jpg")
