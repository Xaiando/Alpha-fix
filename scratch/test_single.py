"""
Single-file test processor. Pass filename as argument.
Writes result to processed/ using the same naming as batch_process.py.
"""
import sys
import shutil
import cv2
import numpy as np
from pathlib import Path
from collections import Counter

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

src_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
out_dir = src_dir / "processed"
out_dir.mkdir(exist_ok=True)

# --- Paste detect_checkerboard_fast from batch_process ---
def detect_checkerboard_fast(img, mask):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corner_pixels = gray[mask]
    if len(corner_pixels) == 0:
        return 999.0, 8.0, 0.0
    pixel_data = corner_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min, color_max = min(c1, c2), max(c1, c2)
    y_indices, x_indices = np.where(mask)
    corner_vals = gray[mask].astype(np.float32)
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
    # Stage 1 float
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
    # Stage 2 fine
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
    mae = 1.0 / f_score
    return mae, f_size, color_max - color_min

def detect_background_type(file_path):
    ext = file_path.suffix.lower()
    if ext in (".png", ".webp"):
        img_u = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
        if img_u is not None and len(img_u.shape) == 3 and img_u.shape[2] == 4:
            if np.any(img_u[:, :, 3] < 255):
                return "already_transparent", "has alpha"
    img = cv2.imread(str(file_path)) if ext not in (".mp4",) else None
    if img is None:
        cap = cv2.VideoCapture(str(file_path))
        ok, img = cap.read(); cap.release()
        if not ok: return "fallback", "unreadable"
    h, w = img.shape[:2]
    cw = min(64, h // 4, w // 4)
    mask = np.zeros((h, w), dtype=bool)
    mask[:cw, :cw] = True
    mask[:cw, -cw:] = True
    cp = img[mask]
    std = np.max(np.std(cp, axis=0))
    mean_bgr = np.mean(cp, axis=0)
    mean_lab = cv2.cvtColor(np.uint8([[mean_bgr]]), cv2.COLOR_BGR2LAB)[0, 0]
    L, A, B = float(mean_lab[0]), float(mean_lab[1]), float(mean_lab[2])
    is_solid = std < 6.0
    is_neutral = abs(A - 128) < 10 and abs(B - 128) < 10
    checker_mae, best_size, color_diff = detect_checkerboard_fast(img, mask)
    is_checker = (not is_solid) and checker_mae < 16.0 and color_diff > 15.0
    if is_solid:
        return ("solid_neutral" if is_neutral else "solid_chroma"), f"std={std:.1f}"
    if is_checker:
        return "checkerboard", f"size={best_size:.1f}, MAE={checker_mae:.1f}, diff={color_diff:.1f}"
    return "fallback", f"std={std:.1f}"


def process_file(file_path, config_override=None):
    """Process a single file and write to out_dir. Returns output path."""
    stem = file_path.stem
    ext = file_path.suffix.lower()
    output_base_name = stem  # single file, no collision worries

    bg_type, bg_details = detect_background_type(file_path)
    print(f"  Background: {bg_type} ({bg_details})")

    if bg_type == "already_transparent":
        dst = out_dir / f"{output_base_name}.png"
        shutil.copy2(file_path, dst)
        print(f"  -> Copied directly to {dst.name}")
        return dst

    if config_override:
        config = config_override
    elif bg_type in ("solid_neutral", "solid_neutral_overflow"):
        config = AlphaFix2Config(mode="subject", subject_low=0.8, subject_high=2.5,
                                  anchor_blur_sigma=1.0, export_alpha_matte=True)
    elif bg_type == "checkerboard":
        config = AlphaFix2Config(mode="overlay", overlay_method="checkerboard",
                                  checkerboard_low=10.0, checkerboard_high=20.0,
                                  export_alpha_matte=True)
    else:
        config = AlphaFix2Config(mode="overlay", overlay_method="auto_hole",
                                  export_alpha_matte=True)

    print(f"  Config: mode={config.mode}, method={getattr(config, 'overlay_method', 'n/a')}")
    service = AlphaFix2Service(config)

    is_video = ext in (".mp4", ".mov", ".avi", ".mkv")
    if is_video:
        from scratch.batch_process import compile_video
        import tempfile, os
        rgba_dir = Path(tempfile.mkdtemp())
        try:
            def progress(done, total):
                if done % 24 == 0 or done == total:
                    print(f"    Frame {done}/{total}")
            summary = service.export_sequence(file_path, rgba_dir, progress_callback=progress)
            webm_out = out_dir / f"{output_base_name}.webm"
            mov_out  = out_dir / f"{output_base_name}.mov"
            compile_video(rgba_dir, summary.fps or 24.0, webm_out, "webm")
            compile_video(rgba_dir, summary.fps or 24.0, mov_out, "prores")
            print(f"  -> {webm_out.name}, {mov_out.name}")
            return webm_out
        finally:
            import shutil as _sh
            _sh.rmtree(rgba_dir, ignore_errors=True)
    else:
        img = cv2.imread(str(file_path))
        result = service.process_frame(img)
        dst = out_dir / f"{output_base_name}.png"
        rgba = result.rgba
        cv2.imwrite(str(dst), cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
        print(f"  -> {dst.name}")
        return dst


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_single.py <filename>")
        sys.exit(1)
    fname = sys.argv[1]
    fp = src_dir / fname
    if not fp.exists():
        print(f"File not found: {fp}")
        sys.exit(1)
    print(f"Processing: {fp.name}")
    out = process_file(fp)
    print(f"Done: {out}")
