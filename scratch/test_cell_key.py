import cv2
import numpy as np

def test_key():
    file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
    img_in = cv2.imread(file_path)
    h, w = img_in.shape[:2]
    gray = cv2.cvtColor(img_in, cv2.COLOR_BGR2GRAY)
    
    # 1. Fit grid parameters on top corners
    corner_w = min(256, h // 4, w // 4)
    top_mask = np.zeros((h, w), dtype=bool)
    top_mask[:corner_w, :corner_w] = True
    top_mask[:corner_w, -corner_w:] = True
    
    top_pixels = gray[top_mask]
    pixel_data = top_pixels.astype(np.float32).reshape(-1, 1)
    
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, _, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    
    y_top, x_top = np.where(top_mask)
    top_vals = gray[top_mask].astype(np.float32)
    
    # Coarse search
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
                    
    # Stage 1 coarse float search
    stage1_best_score = best_score
    stage1_size = best_size
    stage1_off_x = best_off_x
    stage1_off_y = best_off_y
    for size_f in np.arange(best_size - 1.5, best_size + 1.6, 0.1):
        if size_f < 4:
            continue
        for off_x_f in np.arange(best_off_x - 4.0, best_off_x + 4.1, 1.0):
            for off_y_f in np.arange(best_off_y - 4.0, best_off_y + 4.1, 1.0):
                phase = (np.floor((x_top - off_x_f) / size_f) + np.floor((y_top - off_y_f) / size_f)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(top_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > stage1_best_score:
                    stage1_best_score = score
                    stage1_size = size_f
                    stage1_off_x = off_x_f
                    stage1_off_y = off_y_f
                    
    # Stage 2 fine float search
    fine_best_score = stage1_best_score
    fine_size = stage1_size
    fine_off_x = stage1_off_x
    fine_off_y = stage1_off_y
    for size_f in np.arange(stage1_size - 0.15, stage1_size + 0.16, 0.01):
        if size_f < 4:
            continue
        for off_x_f in np.arange(stage1_off_x - 1.0, stage1_off_x + 1.1, 0.2):
            for off_y_f in np.arange(stage1_off_y - 1.0, stage1_off_y + 1.1, 0.2):
                phase = (np.floor((x_top - off_x_f) / size_f) + np.floor((y_top - off_y_f) / size_f)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(top_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > fine_best_score:
                    fine_best_score = score
                    fine_size = size_f
                    fine_off_x = off_x_f
                    fine_off_y = off_y_f
                    
    size = fine_size
    off_x = fine_off_x
    off_y = fine_off_y
    
    # Calculate colors from TOP-LEFT corner ONLY
    tl_mask = np.zeros((h, w), dtype=bool)
    tl_mask[:corner_w, :corner_w] = True
    
    y_all, x_all = np.indices((h, w))
    phase_all_A = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2
    
    corner_bgr_pixels = img_in[tl_mask]
    corner_phases_A = phase_all_A[tl_mask]
    
    p0_pixels = corner_bgr_pixels[corner_phases_A == 0]
    p1_pixels = corner_bgr_pixels[corner_phases_A == 1]
    
    color1_bgr = np.mean(p0_pixels, axis=0) if len(p0_pixels) > 0 else np.array([120.0, 120.0, 120.0])
    color2_bgr = np.mean(p1_pixels, axis=0) if len(p1_pixels) > 0 else np.array([180.0, 180.0, 180.0])
    
    # expected backgrounds for both phases
    expected_A = np.zeros_like(img_in, dtype=np.float32)
    expected_A[phase_all_A == 0] = color1_bgr
    expected_A[phase_all_A == 1] = color2_bgr
    
    expected_B = np.zeros_like(img_in, dtype=np.float32)
    expected_B[phase_all_A == 0] = color2_bgr
    expected_B[phase_all_A == 1] = color1_bgr
    
    # diffs & distances for both phases
    diff_A = img_in.astype(np.float32) - expected_A
    dist_A = np.sqrt(np.sum(diff_A * diff_A, axis=-1))
    
    diff_B = img_in.astype(np.float32) - expected_B
    dist_B = np.sqrt(np.sum(diff_B * diff_B, axis=-1))
    
    # Cell classification grid setup
    cell_x = np.floor((x_all - off_x) / size)
    cell_y = np.floor((y_all - off_y) / size)
    
    min_cx, min_cy = np.min(cell_x), np.min(cell_y)
    cell_x_idx = (cell_x - min_cx).astype(np.int32)
    cell_y_idx = (cell_y - min_cy).astype(np.int32)
    
    num_cx = np.max(cell_x_idx) + 1
    num_cy = np.max(cell_y_idx) + 1
    
    cell_count = np.zeros((num_cy, num_cx), dtype=np.float32)
    np.add.at(cell_count, (cell_y_idx, cell_x_idx), 1.0)
    
    # Sums for both phases
    cell_sum_A = np.zeros((num_cy, num_cx), dtype=np.float32)
    cell_sum_B = np.zeros((num_cy, num_cx), dtype=np.float32)
    np.add.at(cell_sum_A, (cell_y_idx, cell_x_idx), dist_A)
    np.add.at(cell_sum_B, (cell_y_idx, cell_x_idx), dist_B)
    
    grid_mean_A = cell_sum_A / np.maximum(cell_count, 1.0)
    grid_mean_B = cell_sum_B / np.maximum(cell_count, 1.0)
    
    # Phase-invariant cell mean
    grid_mean = np.minimum(grid_mean_A, grid_mean_B)
    
    # Determine best phase for each cell
    cell_best_phase = (grid_mean_B < grid_mean_A).astype(np.float32)
    pixel_best_phase = cell_best_phase[cell_y_idx, cell_x_idx]
    
    # Compute pixel-level dist based on local cell phase
    dist = np.where(pixel_best_phase == 1, dist_B, dist_A)
    dist = cv2.GaussianBlur(dist, (5, 5), 0)
    
    # Pixel-level alpha
    checkerboard_low = 15.0
    checkerboard_high = 25.0
    t = np.clip((dist - checkerboard_low) / (checkerboard_high - checkerboard_low + 1e-6), 0.0, 1.0)
    alpha_pixel = t * t * (3.0 - 2.0 * t)
    
    # Max filter over 3x3 cells
    kernel = np.ones((3, 3), dtype=np.uint8)
    grid_max_neighbor = cv2.dilate(grid_mean, kernel)
    
    is_bg_cell = (grid_max_neighbor < checkerboard_high).astype(np.uint8)
    near_bg_cell = cv2.dilate(is_bg_cell, kernel)
    near_bg_smooth = cv2.resize(near_bg_cell.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    
    alpha = near_bg_smooth * alpha_pixel + (1.0 - near_bg_smooth) * 1.0
    
    # Save processed image
    rgb = cv2.cvtColor(img_in, cv2.COLOR_BGR2RGB)
    alpha_u8 = np.clip(alpha * 255.0, 0.0, 255.0).astype(np.uint8)
    rgba = np.dstack([rgb, alpha_u8])
    
    cv2.imwrite("scratch/grateful_processed.png", cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    print(f"Saved processed test output with phase-invariant keying. Detected size={size:.4f}, offsets=({off_x:.2f}, {off_y:.2f})")

if __name__ == "__main__":
    test_key()
