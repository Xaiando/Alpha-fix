import cv2
import numpy as np
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.pipeline import AlphaFix2Processor

# Load input
file_path = r"C:\Users\Kaged\Movies\Hub\Projects\image-remix\emoji_21_grateful.png"
img_in = cv2.imread(file_path)

# Let's run the float search first to find size and offset
h, w = img_in.shape[:2]
gray = cv2.cvtColor(img_in, cv2.COLOR_BGR2GRAY)

corner_w = min(64, h // 4, w // 4)
mask = np.zeros((h, w), dtype=bool)
mask[:corner_w, :corner_w] = True
mask[:corner_w, -corner_w:] = True

corner_pixels = gray[mask]
pixel_data = corner_pixels.astype(np.float32).reshape(-1, 1)
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
_, _, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
c1, c2 = float(centers[0][0]), float(centers[1][0])
color_min = min(c1, c2)
color_max = max(c1, c2)

y_indices, x_indices = np.where(mask)
corner_vals = gray[mask].astype(np.float32)

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
            mae = np.mean(np.abs(corner_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > best_score:
                best_score = score
                best_size = float(size)
                best_off_x = float(off_x)
                best_off_y = float(off_y)

refined_best_score = best_score
refined_size = best_size
refined_off_x = best_off_x
refined_off_y = best_off_y

for size_f in np.arange(best_size - 1.5, best_size + 1.6, 0.05):
    if size_f < 4:
        continue
    for off_x_f in np.arange(best_off_x - 2.0, best_off_x + 2.1, 0.5):
        for off_y_f in np.arange(best_off_y - 2.0, best_off_y + 2.1, 0.5):
            phase = (np.floor((x_indices - off_x_f) / size_f) + np.floor((y_indices - off_y_f) / size_f)) % 2
            expected = np.where(phase == 0, color_min, color_max)
            mae = np.mean(np.abs(corner_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > refined_best_score:
                refined_best_score = score
                refined_size = size_f
                refined_off_x = off_x_f
                refined_off_y = off_y_f

print(f"Refined size: {refined_size:.4f}, offsets: ({refined_off_x:.2f}, {refined_off_y:.2f})")

# Let's instantiate config with these values
config = AlphaFix2Config(
    mode="overlay",
    overlay_method="checkerboard",
    checkerboard_low=15.0,
    checkerboard_high=25.0,
    checkerboard_size=refined_size,
    checkerboard_offset_x=refined_off_x,
    checkerboard_offset_y=refined_off_y,
    export_alpha_matte=True
)

# Now, we must modify the processor to support floating-point size/offset!
# Let's first test if we run with modified local implementation
# We can copy the processor logic but with float support to test
processor = AlphaFix2Processor(config)

# Temporarily override self._apply_checkerboard_key of processor to support float
# (We will do the same modification in alpha_fix_2/pipeline.py)
def new_apply_checkerboard_key(self, frame_bgr, cfg):
    h, w = frame_bgr.shape[:2]
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
    
    # Use config values
    size = cfg.checkerboard_size
    off_x = cfg.checkerboard_offset_x
    off_y = cfg.checkerboard_offset_y
    
    # Corner mask to fit colors
    corner_w = min(64, h // 4, w // 4)
    corner_mask = np.zeros((h, w), dtype=bool)
    corner_mask[:corner_w, :corner_w] = True
    corner_mask[:corner_w, -corner_w:] = True
    
    y_all, x_all = np.indices((h, w))
    phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2
    
    corner_bgr_pixels = frame_bgr[corner_mask]
    corner_phases = phase_all[corner_mask]
    
    p0_pixels = corner_bgr_pixels[corner_phases == 0]
    p1_pixels = corner_bgr_pixels[corner_phases == 1]
    
    color1_bgr = np.mean(p0_pixels, axis=0) if len(p0_pixels) > 0 else np.array([120.0, 120.0, 120.0])
    color2_bgr = np.mean(p1_pixels, axis=0) if len(p1_pixels) > 0 else np.array([180.0, 180.0, 180.0])
    
    expected_bg = np.zeros_like(frame_bgr, dtype=np.float32)
    expected_bg[phase_all == 0] = color1_bgr
    expected_bg[phase_all == 1] = color2_bgr
    
    diff = frame_bgr.astype(np.float32) - expected_bg
    dist = np.sqrt(np.sum(diff * diff, axis=-1))
    dist = cv2.GaussianBlur(dist, (5, 5), 0)
    
    t = np.clip((dist - cfg.checkerboard_low) / (cfg.checkerboard_high - cfg.checkerboard_low + 1e-6), 0.0, 1.0)
    alpha_pixel = t * t * (3.0 - 2.0 * t)
    
    # Cell-guided classification
    cell_x = np.floor((x_all - off_x) / size)
    cell_y = np.floor((y_all - off_y) / size)
    min_cx = np.min(cell_x)
    min_cy = np.min(cell_y)
    cell_x_idx = (cell_x - min_cx).astype(np.int32)
    cell_y_idx = (cell_y - min_cy).astype(np.int32)
    num_cx = np.max(cell_x_idx) + 1
    num_cy = np.max(cell_y_idx) + 1
    
    cell_sum = np.zeros((num_cy, num_cx), dtype=np.float32)
    cell_count = np.zeros((num_cy, num_cx), dtype=np.float32)
    
    np.add.at(cell_sum, (cell_y_idx, cell_x_idx), dist)
    np.add.at(cell_count, (cell_y_idx, cell_x_idx), 1.0)
    
    grid_mean = cell_sum / np.maximum(cell_count, 1.0)
    
    kernel = np.ones((3, 3), dtype=np.uint8)
    grid_max_neighbor = cv2.dilate(grid_mean, kernel)
    
    # Use checkerboard_high for classifying background cells
    is_bg_cell = (grid_max_neighbor < cfg.checkerboard_high).astype(np.uint8)
    near_bg_cell = cv2.dilate(is_bg_cell, kernel)
    near_bg_smooth = cv2.resize(near_bg_cell.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    
    alpha = near_bg_smooth * alpha_pixel + (1.0 - near_bg_smooth) * 1.0
    
    debug_views = {}
    debug_stats = {}
    return alpha, debug_views, debug_stats

# Apply monkeypatch
import types
processor._apply_checkerboard_key = types.MethodType(new_apply_checkerboard_key, processor)

result = processor.process_frame(img_in)
alpha = result.alpha
rgba = result.rgba

print("Final Alpha stats:")
print("  Transparent count (alpha < 0.5):", np.sum(alpha < 0.5))
print("  Opaque count (alpha >= 0.5):", np.sum(alpha >= 0.5))

# Save the output
cv2.imwrite("scratch/grateful_processed.png", cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
print("Saved final output to scratch/grateful_processed.png")
