import cv2
import numpy as np
import time

file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img = cv2.imread(file_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
h, w = gray.shape

# Get colors from top-left corner
tl_mask = np.zeros((h, w), dtype=bool)
corner_w = 256
tl_mask[:corner_w, :corner_w] = True
pixel_data = gray[tl_mask].astype(np.float32).reshape(-1, 1)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
_, _, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
c1, c2 = float(centers[0][0]), float(centers[1][0])
color_min = min(c1, c2)
color_max = max(c1, c2)
print(f"Colors: {color_min:.1f} / {color_max:.1f}")

def fit_mask_fast(mask_name, mask):
    t0 = time.time()
    y_indices, x_indices = np.where(mask)
    vals = gray[mask].astype(np.float32)
    
    # 1. Coarse search
    best_score = -1.0
    best_size = 16.0
    best_off_x = 0.0
    best_off_y = 0.0
    
    for size in range(4, 65):
        step = max(1, size // 8)
        for off_x in range(0, size, step):
            for off_y in range(0, size, step):
                phase = (np.floor((x_indices - off_x) / size) + np.floor((y_indices - off_y) / size)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > best_score:
                    best_score = score
                    best_size = float(size)
                    best_off_x = float(off_x)
                    best_off_y = float(off_y)
                    
    # 2. Stage 1: Coarse float search
    stage1_best_score = best_score
    stage1_size = best_size
    stage1_off_x = best_off_x
    stage1_off_y = best_off_y
    
    for size_f in np.arange(best_size - 1.5, best_size + 1.6, 0.1):
        if size_f < 4:
            continue
        for off_x_f in np.arange(best_off_x - 4.0, best_off_x + 4.1, 1.0):
            for off_y_f in np.arange(best_off_y - 4.0, best_off_y + 4.1, 1.0):
                phase = (np.floor((x_indices - off_x_f) / size_f) + np.floor((y_indices - off_y_f) / size_f)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > stage1_best_score:
                    stage1_best_score = score
                    stage1_size = size_f
                    stage1_off_x = off_x_f
                    stage1_off_y = off_y_f
                    
    # 3. Stage 2: Fine float search
    fine_best_score = stage1_best_score
    fine_size = stage1_size
    fine_off_x = stage1_off_x
    fine_off_y = stage1_off_y
    
    for size_f in np.arange(stage1_size - 0.15, stage1_size + 0.16, 0.01):
        if size_f < 4:
            continue
        for off_x_f in np.arange(stage1_off_x - 1.0, stage1_off_x + 1.1, 0.2):
            for off_y_f in np.arange(stage1_off_y - 1.0, stage1_off_y + 1.1, 0.2):
                phase = (np.floor((x_indices - off_x_f) / size_f) + np.floor((y_indices - off_y_f) / size_f)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > fine_best_score:
                    fine_best_score = score
                    fine_size = size_f
                    fine_off_x = off_x_f
                    fine_off_y = off_y_f
                    
    dt = time.time() - t0
    print(f"Corner {mask_name} ({dt:.3f}s): size={fine_size:.4f}, offset=({fine_off_x:.2f}, {fine_off_y:.2f}), MAE={1.0/fine_best_score:.4f}")
    return fine_size, fine_off_x, fine_off_y

# 1. Top-Left
m_tl = np.zeros((h, w), dtype=bool)
m_tl[:corner_w, :corner_w] = True
fit_mask_fast("Top-Left", m_tl)

# 2. Top-Right
m_tr = np.zeros((h, w), dtype=bool)
m_tr[:corner_w, -corner_w:] = True
fit_mask_fast("Top-Right", m_tr)

# 3. Bottom-Left
m_bl = np.zeros((h, w), dtype=bool)
m_bl[-corner_w:, :corner_w] = True
fit_mask_fast("Bottom-Left", m_bl)

# 4. Bottom-Right
m_br = np.zeros((h, w), dtype=bool)
m_br[-corner_w:, -corner_w:] = True
fit_mask_fast("Bottom-Right", m_br)

# 5. Combined Top
m_top = np.zeros((h, w), dtype=bool)
m_top[:corner_w, :corner_w] = True
m_top[:corner_w, -corner_w:] = True
fit_mask_fast("Top Corners", m_top)

# 6. Combined All 4
m_all = np.zeros((h, w), dtype=bool)
m_all[:corner_w, :corner_w] = True
m_all[:corner_w, -corner_w:] = True
m_all[-corner_w:, :corner_w] = True
m_all[-corner_w:, -corner_w:] = True
fit_mask_fast("All 4 Corners", m_all)
