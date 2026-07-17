import cv2
import numpy as np
from pathlib import Path
import time

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

def detect_checkerboard_fast(img, mask):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    corner_pixels = gray[mask]
    if len(corner_pixels) == 0:
        return 999.0, 8, 0.0, 0.0, 0.0
        
    pixel_data = corner_pixels.astype(np.float32).reshape(-1, 1)
    
    # Use K-Means (K=2) on corner pixels to find the two colors
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    
    c1, c2 = float(centers[0][0]), float(centers[1][0])
    color_min = min(c1, c2)
    color_max = max(c1, c2)
    
    y_indices, x_indices = np.where(mask)
    corner_vals = gray[mask].astype(np.float32)
    
    best_score = -1.0
    best_size = 8
    best_off_x = 0
    best_off_y = 0
    
    for size in range(4, 65):
        step = max(1, size // 8)
        for off_x in range(0, size, step):
            for off_y in range(0, size, step):
                phase = (((x_indices - off_x) // size) + ((y_indices - off_y) // size)) % 2
                expected = np.where(phase == 0, color_min, color_max)
                mae = np.mean(np.abs(corner_vals - expected))
                score = 1.0 / (mae + 1e-5)
                
                if score > best_score:
                    best_score = score
                    best_size = size
                    best_off_x = off_x
                    best_off_y = off_y
                    
    # Refine search
    for off_x in range(max(0, best_off_x - 2), min(best_size, best_off_x + 3)):
        for off_y in range(max(0, best_off_y - 2), min(best_size, best_off_y + 3)):
            phase = (((x_indices - off_x) // best_size) + ((y_indices - off_y) // best_size)) % 2
            expected = np.where(phase == 0, color_min, color_max)
            mae = np.mean(np.abs(corner_vals - expected))
            score = 1.0 / (mae + 1e-5)
            if score > best_score:
                best_score = score
                best_off_x = off_x
                best_off_y = off_y
                
    mae = 1.0 / best_score
    color_diff = color_max - color_min
    return mae, best_size, color_diff, color_min, color_max

def classify_file(file_path):
    img = get_first_frame(file_path)
    if img is None:
        return {"name": file_path.name, "error": "Could not read frame"}
        
    h, w, c = img.shape
    # Define corner mask (top-left and top-right corners)
    corner_w = min(64, h // 4, w // 4)
    mask = np.zeros((h, w), dtype=bool)
    mask[:corner_w, :corner_w] = True
    mask[:corner_w, -corner_w:] = True
    
    corner_pixels_bgr = img[mask]
    
    # Calculate std of corners in BGR
    std_bgr = np.std(corner_pixels_bgr, axis=0)
    max_std = float(np.max(std_bgr))
    mean_bgr = np.mean(corner_pixels_bgr, axis=0)
    
    # Convert average BGR of corner to LAB
    mean_bgr_pixel = np.uint8([[mean_bgr]])
    mean_lab = cv2.cvtColor(mean_bgr_pixel, cv2.COLOR_BGR2LAB)[0, 0]
    L, A, B = float(mean_lab[0]), float(mean_lab[1]), float(mean_lab[2])
    
    # Fast checkerboard fit
    checker_mae, best_size, color_diff, c_min, c_max = detect_checkerboard_fast(img, mask)
    
    # K-means classification for dominant color
    pixel_data = corner_pixels_bgr.astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(pixel_data, 2, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    
    # Check if either cluster is neutral and represents a significant portion
    labels = labels.flatten()
    c1_size = np.sum(labels == 0)
    c2_size = np.sum(labels == 1)
    
    c1_bgr = centers[0]
    c2_bgr = centers[1]
    
    c1_lab = cv2.cvtColor(np.uint8([[c1_bgr]]), cv2.COLOR_BGR2LAB)[0, 0]
    c2_lab = cv2.cvtColor(np.uint8([[c2_bgr]]), cv2.COLOR_BGR2LAB)[0, 0]
    
    c1_neutral = abs(float(c1_lab[1]) - 128) < 10 and abs(float(c1_lab[2]) - 128) < 10
    c2_neutral = abs(float(c2_lab[1]) - 128) < 10 and abs(float(c2_lab[2]) - 128) < 10
    
    dominant_is_neutral = False
    if c1_size > c2_size:
        dominant_is_neutral = c1_neutral
    else:
        dominant_is_neutral = c2_neutral
        
    any_large_neutral = (c1_neutral and c1_size > 0.3 * len(labels)) or (c2_neutral and c2_size > 0.3 * len(labels))
    
    return {
        "name": file_path.name,
        "max_std": max_std,
        "L": L, "A": A, "B": B,
        "checker_mae": checker_mae,
        "checker_size": best_size,
        "color_diff": color_diff,
        "dominant_is_neutral": dominant_is_neutral,
        "any_large_neutral": any_large_neutral
    }

def main():
    input_dir = Path(r"C:\Users\Kaged\Movies\Hub\Projects\image-remix")
    valid_suffixes = {".mp4", ".png", ".jpg", ".jpeg"}
    all_files = sorted([
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in valid_suffixes
    ])
    
    print(f"Analyzing {len(all_files)} files...")
    t0 = time.time()
    results = []
    for f in all_files:
        res = classify_file(f)
        results.append(res)
    t1 = time.time()
    print(f"Analysis completed in {t1 - t0:.2f} seconds.")
    
    for res in results:
        if "error" in res:
            print(f"{res['name']}: {res['error']}")
            continue
            
        # Classification logic:
        is_solid = res["max_std"] < 6.0
        is_neutral = abs(res["A"] - 128) < 10 and abs(res["B"] - 128) < 10
        
        # Checkerboard check
        is_checker = (not is_solid) and res["checker_mae"] < 16.0 and res["color_diff"] > 15.0
        
        if is_solid:
            if is_neutral:
                category = "solid_neutral"
            else:
                category = "solid_chroma"
        elif is_checker:
            category = f"checkerboard (size={res['checker_size']})"
        elif res["any_large_neutral"]:
            category = "solid_neutral_overflow"
        else:
            category = "fallback(auto_hole)"
            
        print(f"{res['name']:45} | max_std={res['max_std']:5.1f} | A={res['A']:5.1f} B={res['B']:5.1f} | checker_mae={res['checker_mae']:4.1f} diff={res['color_diff']:5.1f} | -> {category}")

if __name__ == "__main__":
    main()
