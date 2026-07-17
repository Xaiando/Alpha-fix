import cv2
import numpy as np

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

def fit_mask(mask_name, mask):
    y_indices, x_indices = np.where(mask)
    vals = gray[mask].astype(np.float32)
    
    best_score = -1.0
    best_size = 16.0
    best_off_x = 0.0
    best_off_y = 0.0
    
    # Grid search for size around 25.6
    for size_f in np.arange(25.0, 26.2, 0.01):
        for off_x_f in np.arange(-2.0, size_f + 2.0, 0.5):
            for off_y_f in np.arange(-2.0, size_f + 2.0, 0.5):
                phase = (np.floor((x_indices - off_x_f) / size_f) + np.floor((y_indices - off_y_f) / size_f)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > best_score:
                    best_score = score
                    best_size = size_f
                    best_off_x = off_x_f
                    best_off_y = off_y_f
                    
    print(f"Corner {mask_name}: size={best_size:.4f}, offset=({best_off_x:.2f}, {best_off_y:.2f}), MAE={1.0/best_score:.4f}")
    return best_size, best_off_x, best_off_y

# 1. Top-Left
m_tl = np.zeros((h, w), dtype=bool)
m_tl[:corner_w, :corner_w] = True
fit_mask("Top-Left", m_tl)

# 2. Top-Right
m_tr = np.zeros((h, w), dtype=bool)
m_tr[:corner_w, -corner_w:] = True
fit_mask("Top-Right", m_tr)

# 3. Bottom-Left
m_bl = np.zeros((h, w), dtype=bool)
m_bl[-corner_w:, :corner_w] = True
fit_mask("Bottom-Left", m_bl)

# 4. Bottom-Right
m_br = np.zeros((h, w), dtype=bool)
m_br[-corner_w:, -corner_w:] = True
fit_mask("Bottom-Right", m_br)

# 5. Combined
m_all = np.zeros((h, w), dtype=bool)
m_all[:corner_w, :corner_w] = True
m_all[:corner_w, -corner_w:] = True
m_all[-corner_w:, :corner_w] = True
m_all[-corner_w:, -corner_w:] = True
fit_mask("All 4 corners", m_all)
