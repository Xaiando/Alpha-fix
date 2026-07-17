import cv2
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service
from alpha_fix_2.pipeline import AlphaFix2Processor

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")

def inspect_file(fname):
    src = src_dir / fname
    img = cv2.imread(str(src))
    h, w = img.shape[:2]
    
    # Run the same service setup
    config = AlphaFix2Config(mode="overlay", overlay_method="checkerboard",
                              checkerboard_low=15.0, checkerboard_high=25.0)
    processor = AlphaFix2Processor(config)
    result = processor.process_frame(img)
    rgba = result.rgba
    alpha = rgba[:, :, 3]
    
    # Now let's extract internal variables by duplicating the pipeline logic
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    params = processor._checkerboard_params
    size = params["size"]
    off_x = params["offset_x"]
    off_y = params["offset_y"]
    color1_bgr = params["color1_bgr"]
    color2_bgr = params["color2_bgr"]
    
    y_all, x_all = np.indices((h, w))
    phase_all = (np.floor((x_all - off_x) / size) + np.floor((y_all - off_y) / size)) % 2
    
    expected_bg = np.zeros_like(img, dtype=np.float32)
    expected_bg[phase_all == 0] = color1_bgr
    expected_bg[phase_all == 1] = color2_bgr
    
    diff = img.astype(np.float32) - expected_bg
    dist = np.sqrt(np.sum(diff * diff, axis=-1))
    dist_blurred = cv2.GaussianBlur(dist, (5, 5), 0)
    
    t = np.clip((dist_blurred - config.checkerboard_low) / (config.checkerboard_high - config.checkerboard_low + 1e-6), 0.0, 1.0)
    alpha_pixel = t * t * (3.0 - 2.0 * t)
    
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
    np.add.at(cell_sum, (cell_y_idx, cell_x_idx), dist_blurred)
    np.add.at(cell_count, (cell_y_idx, cell_x_idx), 1.0)
    grid_mean = cell_sum / np.maximum(cell_count, 1.0)
    
    kernel = np.ones((3, 3), dtype=np.uint8)
    grid_max_neighbor = cv2.dilate(grid_mean, kernel)
    
    is_bg_cell = (grid_max_neighbor < config.checkerboard_high).astype(np.uint8)
    near_bg_cell = cv2.dilate(is_bg_cell, kernel)
    near_bg_smooth = cv2.resize(near_bg_cell.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    
    final_alpha = near_bg_smooth * alpha_pixel + (1.0 - near_bg_smooth) * 1.0
    
    print(f"\n===== Inspecting {fname} =====")
    print(f"  Detected checkerboard size={size:.4f}, offset=({off_x:.2f}, {off_y:.2f})")
    
    corner_size = min(20, h // 8, w // 8)
    corners = {
        "TL": (final_alpha[:corner_size, :corner_size], near_bg_smooth[:corner_size, :corner_size]),
        "TR": (final_alpha[:corner_size, -corner_size:], near_bg_smooth[:corner_size, -corner_size:]),
        "BL": (final_alpha[-corner_size:, :corner_size], near_bg_smooth[-corner_size:, :corner_size]),
        "BR": (final_alpha[-corner_size:, -corner_size:], near_bg_smooth[-corner_size:, -corner_size:])
    }
    
    for name, (alpha_slice, smooth_slice) in corners.items():
        print(f"  Corner {name} - Avg alpha: {np.mean(alpha_slice)*255.0:.1f}/255, Avg smooth_weight: {np.mean(smooth_slice):.2f}")

inspect_file("emoji_waving.jpg")
inspect_file("emoji_thinking_29.jpg")
