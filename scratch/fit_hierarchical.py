import cv2
import numpy as np
from pathlib import Path

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def fit_hierarchical(fname):
    img = cv2.imread(str(src_dir / fname))
    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    corner_w = 96
    
    # 1. TL-only mask
    tl_mask = np.zeros((h, w), dtype=bool)
    tl_mask[:corner_w, :corner_w] = True
    
    pixel_data = gray[tl_mask].astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min, color_max = min(c1, c2), max(c1, c2)
    
    y_tl, x_tl = np.where(tl_mask)
    vals_tl = gray[tl_mask].astype(np.float32)
    
    # Fit coarse size on TL only
    best_score = -1.0
    best_size = 16.0
    best_ox, best_oy = 0.0, 0.0
    
    for s in range(4, 65):
        step = max(1, s // 8)
        for ox in range(0, s, step):
            for oy in range(0, s, step):
                phase = (np.floor((x_tl - ox) / s) + np.floor((y_tl - oy) / s)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals_tl - expected))
                score = 1.0 / (mae + 1e-5)
                if score > best_score:
                    best_score = score
                    best_size = float(s)
                    best_ox = float(ox)
                    best_oy = float(oy)
                    
    # Stage 1 fine on TL only
    s1_score = best_score
    s1_size = best_size
    s1_ox = best_ox
    s1_oy = best_oy
    for sf in np.arange(best_size - 1.5, best_size + 1.6, 0.1):
        if sf < 4: continue
        for oxf in np.arange(best_off_x := best_ox - 4.0, best_ox + 4.1, 1.0):
            for oyf in np.arange(best_off_y := best_oy - 4.0, best_oy + 4.1, 1.0):
                phase = (np.floor((x_tl - oxf) / sf) + np.floor((y_tl - oyf) / sf)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(vals_tl - expected))
                score = 1.0 / (mae + 1e-5)
                if score > s1_score:
                    s1_score = score
                    s1_size = sf
                    s1_ox = oxf
                    s1_oy = oyf
                    
    print(f"\n--- Hierarchical search for {fname} ---")
    print(f"  TL Coarse Size: {s1_size:.2f}, offset: ({s1_ox:.1f}, {s1_oy:.1f})")
    
    # 2. Four corners mask for global rectangular fine tuning
    four_mask = np.zeros((h, w), dtype=bool)
    four_mask[:corner_w, :corner_w] = True
    four_mask[:corner_w, -corner_w:] = True
    four_mask[-corner_w:, :corner_w] = True
    four_mask[-corner_w:, -corner_w:] = True
    
    # We filter out corners with subject pixels
    # E.g. we only include corners whose standard deviation is close to the TL corner's std (std of checkerboard).
    # Since std of TL is around 16.5, any corner with std in [12, 25] is checkerboard.
    corners_definitions = {
        "TL": (0, corner_w, 0, corner_w),
        "TR": (0, corner_w, w - corner_w, w),
        "BL": (h - corner_w, h, 0, corner_w),
        "BR": (h - corner_w, h, w - corner_w, w)
    }
    
    active_mask = np.zeros((h, w), dtype=bool)
    for name, (r0, r1, c0, c1) in corners_definitions.items():
        c_std = np.std(gray[r0:r1, c0:c1])
        if 10.0 < c_std < 30.0:
            active_mask[r0:r1, c0:c1] = True
            print(f"  Including corner {name} (std={c_std:.1f})")
        else:
            print(f"  Excluding corner {name} (std={c_std:.1f}) - likely contaminated")
            
    y_4, x_4 = np.where(active_mask)
    vals_4 = gray[active_mask].astype(np.float32)
    
    best_global_mae = 999.0
    best_sx, best_sy = s1_size, s1_size
    best_gox, best_goy = s1_ox, s1_oy
    
    # Fine search size_x and size_y in [s1_size - 0.2, s1_size + 0.2] with step 0.002
    # offset in [s1_ox/oy - 1.0, s1_ox/oy + 1.0] with step 0.1
    for sx in np.arange(s1_size - 0.2, s1_size + 0.21, 0.002):
        for sy in np.arange(s1_size - 0.2, s1_size + 0.21, 0.002):
            for ox in np.arange(s1_ox - 1.0, s1_ox + 1.1, 0.2):
                for oy in np.arange(s1_oy - 1.0, s1_oy + 1.1, 0.2):
                    phase = (np.floor((x_4 - ox) / sx) + np.floor((y_4 - oy) / sy)) % 2
                    expected = np.where(phase == 0, color_min, color_max)
                    mae = np.mean(np.abs(vals_4 - expected))
                    if mae < best_global_mae:
                        best_global_mae = mae
                        best_sx, best_sy = sx, sy
                        best_gox, best_goy = ox, oy
                        
    print(f"  Best Global Size X: {best_sx:.4f}, Y: {best_sy:.4f}")
    print(f"  Best Global Offset: ({best_gox:.2f}, {best_goy:.2f})")
    print(f"  Global MAE: {best_global_mae:.3f}")
    
    # Individual corner MAEs
    for name, (r0, r1, c0, c1) in corners_definitions.items():
        c_mask = np.zeros((h, w), dtype=bool)
        c_mask[r0:r1, c0:c1] = True
        c_y, c_x = np.where(c_mask)
        c_vals = gray[c_mask].astype(np.float32)
        c_phase = (np.floor((c_x - best_gox) / best_sx) + np.floor((c_y - best_goy) / best_sy)) % 2
        c_expected = np.where(c_phase == 0, color_min, color_max)
        c_mae = np.mean(np.abs(c_vals - c_expected))
        print(f"    Corner {name} MAE: {c_mae:.2f}")

fit_hierarchical("emoji_waving.jpg")
fit_hierarchical("emoji_thinking_29.jpg")
fit_hierarchical("emoji_party.jpg")
