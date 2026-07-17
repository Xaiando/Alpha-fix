"""
Process image files one-at-a-time with audit output.
Skips files already in processed/.
Run this and check results after each batch.
"""
import sys
import shutil
import cv2
import numpy as np
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
out_dir = src_dir / "processed"
out_dir.mkdir(exist_ok=True)

valid_suffixes = {".mp4", ".png", ".jpg", ".jpeg"}
all_files = sorted([f for f in src_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in valid_suffixes])
stem_counts = Counter(f.stem for f in all_files)


def detect_checkerboard_fast(img, mask):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corner_pixels = gray[mask]
    if len(corner_pixels) == 0:
        return 999.0, 8.0, 0.0
        
    y_indices, x_indices = np.where(mask)
    pixel_data = corner_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min, color_max = min(c1, c2), max(c1, c2)
    
    corner_vals = corner_pixels.astype(np.float32)
    best_score, best_size, best_off_x, best_off_y = -1.0, 16.0, 0.0, 0.0
    for s in range(4, 65):
        step = max(1, s // 8)
        for ox in range(0, s, step):
            for oy in range(0, s, step):
                phase = (np.floor((x_indices - ox) / s) + np.floor((y_indices - oy) / s)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(corner_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > best_score:
                    best_score, best_size, best_off_x, best_off_y = score, float(s), float(ox), float(oy)
    s1_score, s1_size, s1_ox, s1_oy = best_score, best_size, best_off_x, best_off_y
    for sf in np.arange(best_size - 1.5, best_size + 1.6, 0.1):
        if sf < 4: continue
        for oxf in np.arange(best_off_x - 4.0, best_off_x + 4.1, 1.0):
            for oyf in np.arange(best_off_y - 4.0, best_off_y + 4.1, 1.0):
                phase = (np.floor((x_indices - oxf) / sf) + np.floor((y_indices - oyf) / sf)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(corner_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > s1_score:
                    s1_score, s1_size, s1_ox, s1_oy = score, sf, oxf, oyf
    f_score, f_size, f_ox, f_oy = s1_score, s1_size, s1_ox, s1_oy
    for sf in np.arange(s1_size - 0.15, s1_size + 0.16, 0.01):
        if sf < 4: continue
        for oxf in np.arange(s1_ox - 1.0, s1_ox + 1.1, 0.2):
            for oyf in np.arange(s1_oy - 1.0, s1_oy + 1.1, 0.2):
                phase = (np.floor((x_indices - oxf) / sf) + np.floor((y_indices - oyf) / sf)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(corner_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > f_score:
                    f_score, f_size, f_ox, f_oy = score, sf, oxf, oyf
    return 1.0 / f_score, f_size, color_max - color_min


def detect_background_type(file_path):
    ext = file_path.suffix.lower()
    if ext in (".png", ".webp"):
        img_u = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
        if img_u is not None and len(img_u.shape) == 3 and img_u.shape[2] == 4:
            if np.any(img_u[:, :, 3] < 255):
                return "already_transparent", "has alpha"
    img = cv2.imread(str(file_path))
    if img is None:
        return "fallback", "unreadable"
    h, w = img.shape[:2]
    cw = min(48, h // 8, w // 8)
    margin = 4
    
    # We construct mask_top and mask_bottom to check for solid vs split background
    mask_top = np.zeros((h, w), dtype=bool)
    mask_top[margin:cw, margin:cw] = True
    mask_top[margin:cw, -cw:-margin] = True
    
    mask_bottom = np.zeros((h, w), dtype=bool)
    mask_bottom[-cw:-margin, margin:cw] = True
    mask_bottom[-cw:-margin, -cw:-margin] = True
    
    cp_top = img[mask_top]
    cp_bottom = img[mask_bottom]
    
    std_top = float(np.max(np.std(cp_top, axis=0)))
    std_bottom = float(np.max(np.std(cp_bottom, axis=0)))
    
    mean_top = np.mean(cp_top, axis=0)
    mean_bottom = np.mean(cp_bottom, axis=0)
    mean_diff = float(np.linalg.norm(mean_top - mean_bottom))
    
    is_solid_top = std_top < 6.0
    is_solid_bottom = std_bottom < 6.0
    
    if is_solid_top and is_solid_bottom:
        is_solid = True
    elif is_solid_top and not is_solid_bottom:
        # Maybe subject touches bottom corners, but top is clean solid background
        is_solid = True
    else:
        is_solid = False
        
    mean_bgr = mean_top
    mean_lab = cv2.cvtColor(np.uint8([[mean_bgr]]), cv2.COLOR_BGR2LAB)[0, 0]
    A, B = float(mean_lab[1]), float(mean_lab[2])
    is_neutral = abs(A - 128) < 10 and abs(B - 128) < 10
    
    # Run checkerboard search on the top mask only
    checker_mae, best_size, color_diff = detect_checkerboard_fast(img, mask_top)
    is_checker = (not is_solid) and checker_mae < 16.0 and color_diff > 15.0
    
    if is_solid:
        return ("solid_neutral" if is_neutral else "solid_chroma"), f"std={std_top:.1f}"
    if is_checker:
        return "checkerboard", f"size={best_size:.1f}, MAE={checker_mae:.1f}, diff={color_diff:.1f}"
    return "fallback", f"std={std_top:.1f}"


def audit_png(path):
    """Return (corner_transparent, center_opaque, issues)."""
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None or img.shape[2] != 4:
        return False, False, ["not RGBA"]
    h, w = img.shape[:2]
    alpha = img[:, :, 3]
    corner_size = min(20, h // 8, w // 8)
    corners_alpha = np.concatenate([
        alpha[:corner_size, :corner_size].flatten(),
        alpha[:corner_size, -corner_size:].flatten(),
        alpha[-corner_size:, :corner_size].flatten(),
        alpha[-corner_size:, -corner_size:].flatten(),
    ])
    center_alpha = alpha[h//2 - 60:h//2 + 60, w//2 - 60:w//2 + 60]
    corner_mean = float(np.mean(corners_alpha))
    center_opaque = float(np.mean(center_alpha > 200))
    issues = []
    if corner_mean > 30:
        issues.append(f"corners not transparent (mean alpha={corner_mean:.0f})")
    if center_opaque < 0.5:
        issues.append(f"center mostly transparent ({center_opaque*100:.0f}% opaque) - subject likely erased")
    return corner_mean < 30, center_opaque >= 0.5, issues


# ---- IMAGE FILES ONLY (no videos for now) ----
image_exts = {".png", ".jpg", ".jpeg"}

# Build list of image files missing from processed
to_process = []
for file_path in all_files:
    if file_path.suffix.lower() not in image_exts:
        continue
    stem = file_path.stem
    ext = file_path.suffix.lower()
    if stem_counts[stem] > 1:
        output_base_name = f"{stem}_{ext.lstrip('.')}"
    else:
        output_base_name = stem
    dst = out_dir / f"{output_base_name}.png"
    if not dst.exists():
        to_process.append((file_path, output_base_name, dst))

print(f"Image files to process: {len(to_process)}")
passed = []
failed = []

for file_path, output_base_name, dst in to_process:
    print(f"\n--- {file_path.name} ---")
    bg_type, bg_details = detect_background_type(file_path)
    print(f"  BG type: {bg_type} ({bg_details})")

    if bg_type == "already_transparent":
        shutil.copy2(file_path, dst)
        print(f"  Copied -> {dst.name}")
        passed.append(file_path.name)
        continue

    if bg_type in ("solid_neutral", "solid_neutral_overflow"):
        config = AlphaFix2Config(mode="subject", subject_low=0.8, subject_high=2.5,
                                  anchor_blur_sigma=1.0, export_alpha_matte=True)
    elif bg_type == "checkerboard":
        # 30/45 range ensures completely transparent corners on compressed checker backgrounds
        config = AlphaFix2Config(mode="overlay", overlay_method="checkerboard",
                                  checkerboard_low=30.0, checkerboard_high=45.0,
                                  export_alpha_matte=True)
    else:
        config = AlphaFix2Config(mode="overlay", overlay_method="auto_hole",
                                  export_alpha_matte=True)

    try:
        service = AlphaFix2Service(config)
        preview = service.preview(file_path)
        rgba = preview.frame_result.rgba
        cv2.imwrite(str(dst), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))

        corner_ok, center_ok, issues = audit_png(dst)
        if issues:
            print(f"  AUDIT FAIL: {'; '.join(issues)}")
            failed.append((file_path.name, issues))
        else:
            print(f"  AUDIT PASS: corners transparent, center opaque")
            passed.append(file_path.name)
    except Exception as e:
        print(f"  ERROR: {e}")
        failed.append((file_path.name, [str(e)]))

print(f"\n{'='*50}")
print(f"Passed: {len(passed)}")
print(f"Failed: {len(failed)}")
if failed:
    print("\nFailed files:")
    for name, issues in failed:
        print(f"  {name}: {'; '.join(issues)}")
