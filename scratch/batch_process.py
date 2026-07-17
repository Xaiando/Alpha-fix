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
    
    # Use K-Means (K=2) on corner pixels to find the two colors
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    
    y_indices, x_indices = np.where(mask)
    corner_vals = gray[mask].astype(np.float32)
    
    # 1. Coarse search on top corners
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
                    
    # 2. Stage 1: Coarse float search (step 0.1 for size, 1.0 for offset)
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
                    
    # 3. Stage 2: Fine float search (step 0.01 for size, 0.2 for offset in a narrow window)
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
    ext = file_path.suffix.lower()
    if ext in (".mp4", ".mov", ".avi", ".mkv"):
        cap = cv2.VideoCapture(str(file_path))
        if not cap.isOpened():
            return None
        ok, frame = cap.read()
        cap.release()
        if ok:
            return frame
    else:
        return cv2.imread(str(file_path))
    return None

def detect_background_type(file_path):
    # Check if the image already has transparency (active alpha channel)
    ext = file_path.suffix.lower()
    if ext in (".png", ".webp"):
        img_unchanged = cv2.imread(str(file_path), cv2.IMREAD_UNCHANGED)
        if img_unchanged is not None and len(img_unchanged.shape) == 3:
            channels = img_unchanged.shape[2]
            if channels == 4:
                alpha = img_unchanged[:, :, 3]
                if np.any(alpha < 255):
                    return "already_transparent", "Image has existing alpha channel"
            elif channels == 2:
                alpha = img_unchanged[:, :, 1]
                if np.any(alpha < 255):
                    return "already_transparent", "Image has existing alpha channel"

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
    
    mean_bgr_pixel = np.uint8([[mean_bgr]])
    mean_lab = cv2.cvtColor(mean_bgr_pixel, cv2.COLOR_BGR2LAB)[0, 0]
    L, A, B = float(mean_lab[0]), float(mean_lab[1]), float(mean_lab[2])
    
    is_solid = max_std < 6.0
    is_neutral = abs(A - 128) < 10 and abs(B - 128) < 10
    
    # Checkerboard check
    checker_mae, best_size, color_diff = detect_checkerboard_fast(img, mask)
    is_checker = (not is_solid) and checker_mae < 16.0 and color_diff > 15.0
    
    if is_solid:
        if is_neutral:
            return "solid_neutral", f"max_std={max_std:.1f}, L={L:.1f}, A={A:.1f}, B={B:.1f}"
        else:
            return "solid_chroma", f"max_std={max_std:.1f}, L={L:.1f}, A={A:.1f}, B={B:.1f}"
            
    if is_checker:
        return "checkerboard", f"size={best_size}, MAE={checker_mae:.1f}, diff={color_diff:.1f}"
        
    # K-means check for subject overflow on a neutral background
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

    # Gather all video and image files
    valid_suffixes = {".mp4", ".png", ".jpg", ".jpeg"}
    all_files = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_suffixes
    ])

    total_files = len(all_files)
    print(f"Found {total_files} files to process in {input_dir}")
    print(f"Output directory: {output_parent}\n")

    # Count occurrences of each stem to detect/resolve collisions
    stem_counts = Counter(f.stem for f in all_files)

    start_time = time.time()
    success_count = 0
    failed_files = []

    for idx, file_path in enumerate(all_files, 1):
        stem = file_path.stem
        ext = file_path.suffix.lower()

        # Resolve output name to prevent collisions between files with same stem
        if stem_counts[stem] > 1:
            ext_suffix = ext.lstrip(".")
            output_base_name = f"{stem}_{ext_suffix}"
        else:
            output_base_name = stem

        print(f"[{idx}/{total_files}] Processing: {file_path.name}")
        
        # 1. Detect background type
        bg_type, bg_details = detect_background_type(file_path)
        print(f"    Detected background: {bg_type} ({bg_details})")
        
        # If the image is already transparent, copy it directly and skip keying
        if bg_type == "already_transparent":
            print("    Image is already transparent. Copying directly...")
            dst_png = output_parent / f"{output_base_name}.png"
            shutil.copy2(file_path, dst_png)
            success_count += 1
            print("  [SUCCESS]\n")
            continue
        
        # 2. Select config
        if bg_type in ("solid_neutral", "solid_neutral_overflow"):
            print("    Selecting config: mode=subject")
            config = AlphaFix2Config(
                mode="subject",
                subject_low=0.8,
                subject_high=2.5,
                anchor_blur_sigma=1.0,
                export_alpha_matte=True
            )
        elif bg_type == "checkerboard":
            print("    Selecting config: mode=overlay, method=checkerboard")
            config = AlphaFix2Config(
                mode="overlay",
                overlay_method="checkerboard",
                checkerboard_low=15.0,
                checkerboard_high=25.0,
                checkerboard_size=0,
                checkerboard_offset_x=-1,
                checkerboard_offset_y=-1,
                export_alpha_matte=True
            )
        else:
            # Fallback (solid_chroma or fallback) -> auto_hole
            print("    Selecting config: mode=overlay, method=auto_hole")
            config = AlphaFix2Config(
                mode="overlay",
                overlay_method="auto_hole",
                export_alpha_matte=True
            )

        # Temp folder for intermediate frames
        temp_dir = output_parent / f".temp_{output_base_name}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Initialize a new service per asset
            service = AlphaFix2Service(config)
            
            def progress(done: int, total: int):
                if done == 1 or done == total or done % max(1, total // 4) == 0:
                    print(f"    Frame progress: {done}/{total}")

            # Export PNG sequence first
            service.export_sequence(
                input_path=file_path,
                output_dir=temp_dir,
                format="png_sequence",
                progress_callback=progress
            )

            is_video = ext == ".mp4"
            if is_video:
                # Read video FPS
                cap = cv2.VideoCapture(str(file_path))
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
                cap.release()

                # Compile to WebM and ProRes
                rgba_dir = temp_dir / "rgba"
                
                print("    Compiling transparent WebM video...")
                webm_output = output_parent / f"{output_base_name}.webm"
                compile_video(rgba_dir, fps, webm_output, "webm")
                
                print("    Compiling transparent ProRes MOV video...")
                prores_output = output_parent / f"{output_base_name}.mov"
                compile_video(rgba_dir, fps, prores_output, "prores")
            else:
                # For images, copy the transparent PNG frame to the main processed directory
                src_png = temp_dir / "rgba" / "frame_00000.png"
                dst_png = output_parent / f"{output_base_name}.png"
                shutil.copy2(src_png, dst_png)

            # Cleanup intermediate frame folder
            shutil.rmtree(temp_dir, ignore_errors=True)
            success_count += 1
            print("  [SUCCESS]\n")
        except Exception as e:
            # Clean up temp folder on failure too
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"  [FAILED] {e}\n")
            failed_files.append((file_path.name, str(e)))

    elapsed = time.time() - start_time
    print("=" * 60)
    print("Batch Processing Finished!")
    print(f"Successfully processed {success_count}/{total_files} files in {elapsed:.2f} seconds.")
    if failed_files:
        print("\nFailed files:")
        for name, err in failed_files:
            print(f"  - {name}: {err}")
    print("=" * 60)

if __name__ == "__main__":
    main()
