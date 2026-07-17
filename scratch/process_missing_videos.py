import os
import time
import cv2
import numpy as np
import shutil
import subprocess
from pathlib import Path
from collections import Counter
from alpha_fix_2.config import AlphaFix2Config
from alpha_fix_2.service import AlphaFix2Service

def compile_video(rgba_dir: Path, fps: float, output_file: Path, codec: str):
    if codec == "webm":
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-auto-alt-ref", "0",
            "-color_range", "pc", "-colorspace", "1", "-color_primaries", "1", "-color_trc", "1",
            str(output_file)
        ]
    elif codec == "prores":
        cmd = [
            "ffmpeg", "-y", "-framerate", str(fps),
            "-i", f"{rgba_dir.as_posix()}/frame_%05d.png",
            "-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le",
            "-color_range", "pc", "-colorspace", "1", "-color_primaries", "1", "-color_trc", "1",
            str(output_file)
        ]
    else:
        return
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

def detect_checkerboard_fast(img, mask):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corner_pixels = gray[mask]
    if len(corner_pixels) == 0:
        return 999.0, 8.0, 0.0
        
    pixel_data = corner_pixels.astype(np.float32).reshape(-1, 1)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    
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
                mae = np.mean(np.abs(corner_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > stage1_best_score:
                    stage1_best_score = score
                    stage1_size = size_f
                    stage1_off_x = off_x_f
                    stage1_off_y = off_y_f
                    
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
                mae = np.mean(np.abs(corner_vals - expected))
                score = 1.0 / (mae + 1e-5)
                if score > fine_best_score:
                    fine_best_score = score
                    fine_size = size_f
                    fine_off_x = off_x_f
                    fine_off_y = off_y_f
                    
    mae = 1.0 / fine_best_score
    color_diff = color_max - color_min
    return mae, fine_size, color_diff

def get_first_frame(file_path):
    cap = cv2.VideoCapture(str(file_path))
    if not cap.isOpened():
        return None
    ok, frame = cap.read()
    cap.release()
    return frame if ok else None

def detect_background_type(file_path):
    img = get_first_frame(file_path)
    if img is None:
        return "fallback", "Error reading frame"
        
    h, w, c = img.shape
    corner_w = min(64, h // 4, w // 4)
    mask = np.zeros((h, w), dtype=bool)
    mask[:corner_w, :corner_w] = True
    mask[:corner_w, -corner_w:] = True
    
    corner_pixels_bgr = img[mask]
    std_bgr = np.std(corner_pixels_bgr, axis=0)
    max_std = float(np.max(std_bgr))
    mean_bgr = np.mean(corner_pixels_bgr, axis=0)
    
    mean_lab = cv2.cvtColor(np.uint8([[mean_bgr]]), cv2.COLOR_BGR2LAB)[0, 0]
    L, A, B = float(mean_lab[0]), float(mean_lab[1]), float(mean_lab[2])
    
    is_solid = max_std < 6.0
    is_neutral = abs(A - 128) < 10 and abs(B - 128) < 10
    
    checker_mae, best_size, color_diff = detect_checkerboard_fast(img, mask)
    is_checker = (not is_solid) and checker_mae < 16.0 and color_diff > 15.0
    
    if is_solid:
        if is_neutral:
            return "solid_neutral", f"max_std={max_std:.1f}, L={L:.1f}, A={A:.1f}, B={B:.1f}"
        else:
            return "solid_chroma", f"max_std={max_std:.1f}, L={L:.1f}, A={A:.1f}, B={B:.1f}"
            
    if is_checker:
        return "checkerboard", f"size={best_size}, MAE={checker_mae:.1f}, diff={color_diff:.1f}"
        
    pixel_data = corner_pixels_bgr.astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    
    labels = labels.flatten()
    c1_size = np.sum(labels == 0)
    c2_size = np.sum(labels == 1)
    
    c1_lab = cv2.cvtColor(np.uint8([[centers[0]]]), cv2.COLOR_BGR2LAB)[0, 0]
    c2_lab = cv2.cvtColor(np.uint8([[centers[1]]]), cv2.COLOR_BGR2LAB)[0, 0]
    
    c1_neutral = abs(float(c1_lab[1]) - 128) < 10 and abs(float(c1_lab[2]) - 128) < 10
    c2_neutral = abs(float(c2_lab[1]) - 128) < 10 and abs(float(c2_lab[2]) - 128) < 10
    
    any_large_neutral = (c1_neutral and c1_size > 0.3 * len(labels)) or (c2_neutral and c2_size > 0.3 * len(labels))
    if any_large_neutral:
        return "solid_neutral_overflow", f"max_std={max_std:.1f}"
        
    return "fallback", f"max_std={max_std:.1f}"

def main():
    input_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
    output_parent = input_dir / "processed"
    output_parent.mkdir(parents=True, exist_ok=True)

    all_files = list(input_dir.iterdir())
    stem_counts = Counter(f.stem for f in all_files if f.is_file())

    video_files = sorted([
        f for f in all_files
        if f.is_file() and f.suffix.lower() == ".mp4"
    ])

    to_process = []
    for file_path in video_files:
        stem = file_path.stem
        ext = file_path.suffix.lower()
        if stem_counts[stem] > 1:
            output_base_name = f"{stem}_{ext.lstrip('.')}"
        else:
            output_base_name = stem
        
        webm_output = output_parent / f"{output_base_name}.webm"
        prores_output = output_parent / f"{output_base_name}.mov"
        
        if not webm_output.exists() or not prores_output.exists():
            to_process.append((file_path, output_base_name, webm_output, prores_output))

    print(f"Found {len(to_process)} videos to process out of {len(video_files)} total videos.")
    if not to_process:
        print("No videos need processing.")
        return

    start_time = time.time()
    success_count = 0
    failed_files = []

    for idx, (file_path, output_base_name, webm_output, prores_output) in enumerate(to_process, 1):
        print(f"[{idx}/{len(to_process)}] Processing video: {file_path.name}")
        bg_type, bg_details = detect_background_type(file_path)
        print(f"    Detected background: {bg_type} ({bg_details})")

        if bg_type in ("solid_neutral", "solid_neutral_overflow"):
            print("    Config: mode=subject")
            config = AlphaFix2Config(
                mode="subject",
                subject_low=0.8,
                subject_high=2.5,
                anchor_blur_sigma=1.0,
                export_alpha_matte=True
            )
        elif bg_type == "checkerboard":
            print("    Config: mode=overlay, method=checkerboard")
            config = AlphaFix2Config(
                mode="overlay",
                overlay_method="checkerboard",
                checkerboard_low=30.0,  # 30/45 range for compressed checkerboard corners
                checkerboard_high=45.0,
                checkerboard_size=0,
                checkerboard_offset_x=-1,
                checkerboard_offset_y=-1,
                export_alpha_matte=True
            )
        else:
            print("    Config: mode=overlay, method=auto_hole")
            config = AlphaFix2Config(
                mode="overlay",
                overlay_method="auto_hole",
                export_alpha_matte=True
            )

        temp_dir = output_parent / f".temp_{output_base_name}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            service = AlphaFix2Service(config)
            
            def progress(done: int, total: int):
                if done == 1 or done == total or done % max(1, total // 4) == 0:
                    print(f"    Frame progress: {done}/{total}")

            service.export_sequence(
                input_path=file_path,
                output_dir=temp_dir,
                format="png_sequence",
                progress_callback=progress
            )

            cap = cv2.VideoCapture(str(file_path))
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
            cap.release()

            rgba_dir = temp_dir / "rgba"
            
            print(f"    Compiling transparent WebM -> {webm_output.name}")
            compile_video(rgba_dir, fps, webm_output, "webm")
            
            print(f"    Compiling transparent ProRes MOV -> {prores_output.name}")
            compile_video(rgba_dir, fps, prores_output, "prores")

            shutil.rmtree(temp_dir, ignore_errors=True)
            success_count += 1
            print("  [SUCCESS]\n")
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"  [FAILED] {e}\n")
            failed_files.append((file_path.name, str(e)))

    elapsed = time.time() - start_time
    print("=" * 60)
    print("Video Processing Finished!")
    print(f"Successfully processed {success_count}/{len(to_process)} videos in {elapsed:.2f} seconds.")
    if failed_files:
        print("\nFailed videos:")
        for name, err in failed_files:
            print(f"  - {name}: {err}")
    print("=" * 60)

if __name__ == "__main__":
    main()
